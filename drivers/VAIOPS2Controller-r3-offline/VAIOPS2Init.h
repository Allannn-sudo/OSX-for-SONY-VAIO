/*
 * Portions Copyright (c) 1999-2000 Apple Computer, Inc. All Rights Reserved.
 * This file contains Original Code and/or Modifications of Original Code as
 * defined in and that are subject to the Apple Public Source License Version
 * 1.1 (the "License"). You may not use this file except in compliance with
 * the License. Please obtain a copy of the License at
 * http://www.apple.com/publicsource and read it before using this file.
 *
 * The Original Code and all software distributed under the License are
 * distributed on an "AS IS" basis, WITHOUT WARRANTY OF ANY KIND, EITHER
 * EXPRESS OR IMPLIED, AND APPLE HEREBY DISCLAIMS ALL SUCH WARRANTIES,
 * INCLUDING WITHOUT LIMITATION, ANY WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE OR NON-INFRINGEMENT. Please see the
 * License for the specific language governing rights and limitations
 * under the License.
 *
 * Project modifications: 2026-10-19; source-only archive of R3-OFFLINE.
 * See NOTICE for the pinned upstream version and dated changes.
 */

/*
 * VAIO Y18C experimental cold-start initialization, 2026-10-19.
 * This file is new code; see NOTICE for the Apple source provenance and
 * protocol references. No ApplePS2Controller instance or virtual ABI changes.
 *
 * Include after defining UInt8/UInt32, inb/outb, IODelay, IOSleep, IOLog and
 * UInt32 VaioPS2NowMS(void). The host protocol simulator supplies the same
 * small interface. Only start() calls this code, before publishing clients;
 * none of these waits holds a spinlock or disables CPU interrupts.
 */
#ifndef VAIO_PS2_INIT_H
#define VAIO_PS2_INIT_H

#define VAIO_PS2_BUILD "VAIO-Y18C-PS2-R3-OFFLINE-20261019"

struct VaioPS2InitResult
{
    bool transportSafe;
    bool keyboardReady;
    bool mouseReady;
    bool initialCTRValid;
    bool finalCTRValid;
    UInt8 initialCTR;
    UInt8 finalCTR;
    UInt8 keyboardTest;
    UInt8 mouseTest;
    UInt32 elapsedMS;
    UInt32 discardedBytes;
    const char *failureStage;
};

struct VaioPS2InitContext
{
    VaioPS2InitResult *result;
    UInt32 startMS;
    UInt32 loggedBytes;
};

enum {
    kVaioPS2TotalMS = 20000,
    kVaioPS2ControllerMS = 500,
    kVaioPS2AckMS = 200,
    kVaioPS2ResetAckMS = 1000,
    kVaioPS2BATMS = 4000,
    kVaioPS2IDMS = 500,
    kVaioPS2FlushMS = 50,
    kVaioPS2MaxBytes = 64,
    kVaioPS2MaxByteLogs = 192,
    kVaioPS2Control = -1,
    kVaioPS2Keyboard = 0,
    kVaioPS2Mouse = 1
};

static UInt32 VaioPS2Elapsed(VaioPS2InitContext *context)
{
    /* Unsigned subtraction also handles the 32-bit millisecond wrap. */
    return VaioPS2NowMS() - context->startMS;
}

static void VaioPS2Failure(VaioPS2InitContext *context,
                           const char *stage, const char *reason)
{
    context->result->failureStage = stage;
    IOLog(VAIO_PS2_BUILD ": stage=%s failure=%s elapsed-ms=%lu\n",
          stage, reason, (unsigned long)VaioPS2Elapsed(context));
}

static bool VaioPS2WithinBudget(VaioPS2InitContext *context,
                                const char *stage)
{
    if (VaioPS2Elapsed(context) < kVaioPS2TotalMS) return true;
    context->result->transportSafe = false;
    VaioPS2Failure(context, stage, "total-budget-exhausted");
    return false;
}

static void VaioPS2LogByte(VaioPS2InitContext *context, const char *stage,
                          UInt8 status, UInt8 byte)
{
    /* Raw byte logging is strictly limited to the cold-start path. */
    if (context->loggedBytes < kVaioPS2MaxByteLogs)
        IOLog(VAIO_PS2_BUILD ": stage=%s rx-status=0x%02x rx=0x%02x\n",
              stage, (unsigned)status, (unsigned)byte);
    else if (context->loggedBytes == kVaioPS2MaxByteLogs)
        IOLog(VAIO_PS2_BUILD ": startup-byte-log-limit reached\n");
    ++context->loggedBytes;
}

static bool VaioPS2WaitWritable(VaioPS2InitContext *context,
                                const char *stage)
{
    UInt32 began = VaioPS2NowMS();
    while (VaioPS2WithinBudget(context, stage))
    {
        if (!(inb(0x64) & 0x02)) return true;
        if (VaioPS2NowMS() - began >= kVaioPS2ControllerMS)
        {
            context->result->transportSafe = false;
            VaioPS2Failure(context, stage, "controller-input-busy");
            return false;
        }
        IOSleep(1);
    }
    return false;
}

static bool VaioPS2Write(VaioPS2InitContext *context,
                         const char *stage, UInt8 port, UInt8 byte)
{
    if (!VaioPS2WaitWritable(context, stage)) return false;
    outb(port, byte);
    IODelay(7);
    return true;
}

static bool VaioPS2Flush(VaioPS2InitContext *context, const char *stage)
{
    UInt32 began = VaioPS2NowMS();
    UInt32 count = 0;
    while (VaioPS2WithinBudget(context, stage))
    {
        UInt8 status = inb(0x64);
        if (!(status & 0x01))
        {
            IOLog(VAIO_PS2_BUILD ": stage=%s flushed=%lu\n", stage,
                  (unsigned long)count);
            return true;
        }
        if (count >= kVaioPS2MaxBytes ||
            VaioPS2NowMS() - began >= kVaioPS2FlushMS)
        {
            context->result->transportSafe = false;
            VaioPS2Failure(context, stage, "output-flood");
            return false;
        }
        IODelay(7);
        UInt8 byte = inb(0x60);
        VaioPS2LogByte(context, stage, status, byte);
        ++count;
        ++context->result->discardedBytes;
        IODelay(7);
    }
    return false;
}

static bool VaioPS2Read(VaioPS2InitContext *context, const char *stage,
                        int stream, UInt32 timeoutMS, UInt8 *reply)
{
    UInt32 began = VaioPS2NowMS();
    UInt32 count = 0;
    while (VaioPS2WithinBudget(context, stage))
    {
        if (VaioPS2NowMS() - began >= timeoutMS)
        {
            VaioPS2Failure(context, stage, "response-timeout");
            return false;
        }
        UInt8 status = inb(0x64);
        if (!(status & 0x01))
        {
            IOSleep(1);
            continue;
        }
        IODelay(7);
        UInt8 byte = inb(0x60);
        VaioPS2LogByte(context, stage, status, byte);
        if (++count > kVaioPS2MaxBytes)
        {
            context->result->transportSafe = false;
            VaioPS2Failure(context, stage, "response-flood");
            return false;
        }
        /* CONTROL replies (20/AB/A9) are not mouse-device replies, even
         * for A9. Do not filter CONTROL by the AUX status bit. Device
         * responses, however, must come from their own input stream. */
        bool requested = stream == kVaioPS2Control ||
            ((status & 0x20) ? stream == kVaioPS2Mouse :
                               stream == kVaioPS2Keyboard);
        if ((status & 0xc0) || !requested)
        {
            ++context->result->discardedBytes;
            continue;
        }
        *reply = byte;
        return true;
    }
    return false;
}

static bool VaioPS2ControlReply(VaioPS2InitContext *context,
                                const char *stage, UInt8 command,
                                UInt8 *reply)
{
    IOLog(VAIO_PS2_BUILD ": stage=%s controller-command=0x%02x\n",
          stage, (unsigned)command);
    return VaioPS2Write(context, stage, 0x64, command) &&
           VaioPS2Read(context, stage, kVaioPS2Control,
                       kVaioPS2ControllerMS, reply);
}

static bool VaioPS2SetCTR(VaioPS2InitContext *context,
                         const char *stage, UInt8 commandByte)
{
    UInt8 reply = 0;
    IOLog(VAIO_PS2_BUILD ": stage=%s ctr-write=0x%02x\n", stage,
          (unsigned)commandByte);
    if (!VaioPS2Write(context, stage, 0x64, 0x60) ||
        !VaioPS2Write(context, stage, 0x60, commandByte)) return false;
    if (!VaioPS2ControlReply(context, stage, 0x20, &reply))
    {
        context->result->transportSafe = false;
        return false;
    }
    IOLog(VAIO_PS2_BUILD ": stage=%s ctr-readback=0x%02x mask=0x73\n",
          stage, (unsigned)reply);
    if ((reply & 0x73) != (commandByte & 0x73))
    {
        context->result->transportSafe = false;
        VaioPS2Failure(context, stage, "ctr-readback-mismatch");
        return false;
    }
    context->result->finalCTR = reply;
    context->result->finalCTRValid = true;
    return true;
}

static bool VaioPS2DeviceCommand(VaioPS2InitContext *context,
                                 const char *stage, int stream,
                                 UInt8 command, UInt8 expected,
                                 UInt32 timeoutMS)
{
    UInt8 reply = 0;
    for (unsigned attempt = 0; attempt != 2; ++attempt)
    {
        IOLog(VAIO_PS2_BUILD ": stage=%s stream=%s command=0x%02x attempt=%u\n",
              stage, stream == kVaioPS2Mouse ? "AUX" : "KBD",
              (unsigned)command, attempt + 1);
        if (stream == kVaioPS2Mouse &&
            !VaioPS2Write(context, stage, 0x64, 0xd4)) return false;
        if (!VaioPS2Write(context, stage, 0x60, command) ||
            !VaioPS2Read(context, stage, stream, timeoutMS, &reply))
            return false;
        if (reply == expected) return true;
        if (reply == 0xfe && attempt == 0)
        {
            IOLog(VAIO_PS2_BUILD ": stage=%s device-requested-resend\n", stage);
            continue;
        }
        VaioPS2Failure(context, stage, "unexpected-response");
        return false;
    }
    return false;
}

static bool VaioPS2BAT(VaioPS2InitContext *context, const char *stage,
                      int stream)
{
    UInt8 reply = 0;
    if (!VaioPS2Read(context, stage, stream, kVaioPS2BATMS, &reply))
        return false;
    if (reply == 0xaa) return true;
    VaioPS2Failure(context, stage, "BAT-not-AA");
    return false;
}

static bool VaioPS2ColdInit(VaioPS2InitResult *result)
{
    VaioPS2InitContext context;
    context.result = result;
    context.startMS = VaioPS2NowMS();
    context.loggedBytes = 0;
    result->transportSafe = true;
    result->keyboardReady = false;
    result->mouseReady = false;
    result->initialCTRValid = false;
    result->finalCTRValid = false;
    result->initialCTR = 0;
    result->finalCTR = 0;
    result->keyboardTest = 0xff;
    result->mouseTest = 0xff;
    result->elapsedMS = 0;
    result->discardedBytes = 0;
    result->failureStage = "none";
    UInt8 savedCTR = 0;
    UInt8 previousCTR = 0;
    bool havePreviousCTR = false;
    bool stableCTR = false;
    UInt32 ctrBegan = 0;
    UInt8 reply = 0;
    UInt8 baseCTR = 0;
    bool keyboardReset = false;
    bool mouseReset = false;
    bool mouseID = false;

    IOLog(VAIO_PS2_BUILD ": cold-init begin status=0x%02x budget-ms=%u; "
          "no controller-AA-selftest\n", (unsigned)inb(0x64),
          (unsigned)kVaioPS2TotalMS);

    /* AD/A7 inhibit the interfaces without waiting for a device ACK. */
    if (!VaioPS2Write(&context, "inhibit-keyboard", 0x64, 0xad) ||
        !VaioPS2Write(&context, "inhibit-mouse", 0x64, 0xa7) ||
        !VaioPS2Flush(&context, "initial-flush")) goto finished;

    /* Two equal controller snapshots while both clocks are inhibited.
     * A timeout is never represented as a valid zero command byte. */
    ctrBegan = VaioPS2NowMS();
    for (unsigned attempt = 0; attempt != 10; ++attempt)
    {
        if (VaioPS2NowMS() - ctrBegan >= 2000) break;
        if (!VaioPS2ControlReply(&context, "get-ctr", 0x20, &savedCTR))
        {
            if (!result->transportSafe) goto finished;
            havePreviousCTR = false;
            continue;
        }
        if (havePreviousCTR && savedCTR == previousCTR)
        {
            stableCTR = true;
            break;
        }
        previousCTR = savedCTR;
        havePreviousCTR = true;
    }
    if (!stableCTR)
    {
        result->transportSafe = false;
        VaioPS2Failure(&context, "get-ctr", "no-stable-controller-reply");
        goto finished;
    }
    result->initialCTR = savedCTR;
    result->initialCTRValid = true;
    /* Preserve unrelated bits, force translation, disable IRQ1/IRQ12. */
    baseCTR = (savedCTR & ~0x03) | 0x40;
    if (!VaioPS2SetCTR(&context, "quiesce-ctr", baseCTR | 0x30))
        goto finished;

    /* Port test replies are controller data. Nonzero/missing replies are
     * logged but do not veto a later device handshake or plugin probe. */
    if (VaioPS2ControlReply(&context, "keyboard-interface-test", 0xab, &reply))
    {
        result->keyboardTest = reply;
        if (reply != 0)
            VaioPS2Failure(&context, "keyboard-interface-test", "nonzero-result");
    }
    if (!result->transportSafe) goto finished;
    if (VaioPS2ControlReply(&context, "mouse-interface-test", 0xa9, &reply))
    {
        result->mouseTest = reply;
        if (reply != 0)
            VaioPS2Failure(&context, "mouse-interface-test", "nonzero-result");
    }
    if (!result->transportSafe) goto finished;

    /* Port-test leftovers and late device data cannot be mistaken for a
     * raw CTR reply at a channel boundary. Never flush inside FF ACK/BAT. */
    if (!VaioPS2Write(&context, "before-keyboard-inhibit", 0x64, 0xad) ||
        !VaioPS2Write(&context, "before-keyboard-inhibit", 0x64, 0xa7) ||
        !VaioPS2Flush(&context, "before-keyboard-flush")) goto finished;
    /* Isolate each handshake from the other device's asynchronous data. */
    if (!VaioPS2SetCTR(&context, "keyboard-clock", (baseCTR & ~0x10) | 0x20))
        goto finished;
    keyboardReset = VaioPS2DeviceCommand(&context, "keyboard-reset-ack",
        kVaioPS2Keyboard, 0xff, 0xfa, kVaioPS2ResetAckMS);
    if (keyboardReset)
        keyboardReset = VaioPS2BAT(&context, "keyboard-reset-BAT", kVaioPS2Keyboard);
    if (!result->transportSafe) goto finished;
    if (keyboardReset &&
        VaioPS2DeviceCommand(&context, "keyboard-disable", kVaioPS2Keyboard,
                             0xf5, 0xfa, kVaioPS2AckMS) &&
        VaioPS2DeviceCommand(&context, "keyboard-echo", kVaioPS2Keyboard,
                             0xee, 0xee, kVaioPS2AckMS))
        result->keyboardReady = true;
    if (!result->transportSafe) goto finished;

    if (!VaioPS2Write(&context, "before-mouse-inhibit", 0x64, 0xad) ||
        !VaioPS2Write(&context, "before-mouse-inhibit", 0x64, 0xa7) ||
        !VaioPS2Flush(&context, "before-mouse-flush") ||
        !VaioPS2SetCTR(&context, "mouse-clock", (baseCTR & ~0x20) | 0x10))
        goto finished;
    mouseReset = VaioPS2DeviceCommand(&context, "mouse-reset-ack",
        kVaioPS2Mouse, 0xff, 0xfa, kVaioPS2ResetAckMS);
    if (mouseReset)
        mouseReset = VaioPS2BAT(&context, "mouse-reset-BAT", kVaioPS2Mouse);
    if (!result->transportSafe) goto finished;
    if (mouseReset)
    {
        mouseID = VaioPS2Read(&context, "mouse-reset-ID", kVaioPS2Mouse,
                              kVaioPS2IDMS, &reply);
        if (mouseID && reply != 0)
            IOLog(VAIO_PS2_BUILD ": stage=mouse-reset-ID unusual-ID=0x%02x\n",
                  (unsigned)reply);
        /* Even a missing ID tail need not stop the original plugin probe. */
        if (VaioPS2DeviceCommand(&context, "mouse-defaults", kVaioPS2Mouse,
                                 0xf6, 0xfa, kVaioPS2AckMS) &&
            VaioPS2DeviceCommand(&context, "mouse-disable", kVaioPS2Mouse,
                                 0xf5, 0xfa, kVaioPS2AckMS) && mouseID)
            result->mouseReady = true;
    }
    if (!result->transportSafe) goto finished;

    /* Flush only after finishing each reset response sequence; never
     * between FF's ACK and BAT/ID. End in the old plugins' expected state:
     * clocks enabled, IRQs disabled, set-1 translation enabled. */
    if (!VaioPS2Write(&context, "final-inhibit-keyboard", 0x64, 0xad) ||
        !VaioPS2Write(&context, "final-inhibit-mouse", 0x64, 0xa7) ||
        !VaioPS2Flush(&context, "final-flush") ||
        !VaioPS2Write(&context, "enable-keyboard-clock", 0x64, 0xae) ||
        !VaioPS2Write(&context, "enable-mouse-clock", 0x64, 0xa8) ||
        !VaioPS2SetCTR(&context, "final-ctr", baseCTR & ~0x30))
        goto finished;

finished:
    result->elapsedMS = VaioPS2Elapsed(&context);
    IOLog(VAIO_PS2_BUILD ": cold-init end transport=%s keyboard=%s mouse=%s "
          "initial-ctr-valid=%u initial-ctr=0x%02x final-ctr-valid=%u "
          "final-ctr=0x%02x elapsed-ms=%lu discarded=%lu last-failure=%s\n",
          result->transportSafe ? "safe" : "unsafe",
          result->keyboardReady ? "handshake-ok" : "probe-required",
          result->mouseReady ? "handshake-ok" : "probe-required",
          (unsigned)result->initialCTRValid, (unsigned)result->initialCTR,
          (unsigned)result->finalCTRValid, (unsigned)result->finalCTR,
          (unsigned long)result->elapsedMS,
          (unsigned long)result->discardedBytes, result->failureStage);
    return result->transportSafe;
}

#endif /* VAIO_PS2_INIT_H */
