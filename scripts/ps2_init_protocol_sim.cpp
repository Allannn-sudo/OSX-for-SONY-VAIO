// Host-only protocol model: no hardware I/O and no kernel code is loaded.
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <deque>
#include <string>
#include <vector>

typedef unsigned char UInt8;
typedef unsigned int UInt32;
typedef unsigned long long UInt64;

struct Reply { UInt8 byte; bool aux; UInt64 at; };
struct Mock8042 {
    UInt64 now;
    UInt8 ctr;
    bool ctrWrite, auxWrite, busy, flood, silentControl, silentKeyboard, silentMouse, badBAT;
    bool mouseRepliesAsKeyboard, resendMouseReset;
    unsigned int mouseResets;
    unsigned long keyboardBATms, mouseBATms;
    unsigned int writes, controlTests;
    std::deque<Reply> replies;
    std::vector<unsigned int> deviceWrites;
    Mock8042() : now(0), ctr(0x47), ctrWrite(false), auxWrite(false), busy(false),
        flood(false), silentControl(false), silentKeyboard(false), silentMouse(false),
        badBAT(false), mouseRepliesAsKeyboard(false), resendMouseReset(false), mouseResets(0),
        keyboardBATms(20), mouseBATms(20), writes(0), controlTests(0) {}
    void reply(UInt8 byte, bool aux, unsigned long delayMS = 0) {
        Reply value = {byte, aux, now + UInt64(delayMS) * 1000};
        replies.push_back(value);
    }
    UInt8 status() {
        if (busy) return 0x02;
        if (flood) return 0x21;
        if (!replies.empty() && replies.front().at <= now)
            return UInt8(0x01 | (replies.front().aux ? 0x20 : 0));
        return 0;
    }
    UInt8 data() {
        if (flood) return 0xaa;
        assert(!replies.empty() && replies.front().at <= now);
        UInt8 byte = replies.front().byte;
        replies.pop_front();
        return byte;
    }
    void command(UInt8 byte) {
        ++writes;
        assert(!busy);
        switch (byte) {
        case 0xad: ctr |= 0x10; break;
        case 0xa7: ctr |= 0x20; break;
        case 0xae: ctr &= ~0x10; break;
        case 0xa8: ctr &= ~0x20; break;
        case 0x20: if (!silentControl) reply(ctr, false); break;
        case 0x60: ctrWrite = true; break;
        case 0xd4: auxWrite = true; break;
        case 0xab: case 0xa9:
            // Both controller port-test results use CONTROL/KBD output.
            ++controlTests; reply(0, false); break;
        case 0xaa:
            // Self-test is optional, and this model emulates CTR reset.
            ctr = 0x30; reply(0x55, false); break;
        default:
            std::fprintf(stderr, "Unexpected controller command %02x\n", byte);
            std::abort();
        }
    }
    void output(UInt8 byte) {
        ++writes;
        assert(!busy);
        if (ctrWrite) { ctrWrite = false; ctr = byte; return; }
        bool aux = auxWrite;
        auxWrite = false;
        deviceWrites.push_back((aux ? 0x100 : 0) | byte);
        // No device command can succeed while its channel clock is disabled.
        if (ctr & (aux ? 0x20 : 0x10)) return;
        if ((aux && silentMouse) || (!aux && silentKeyboard)) return;
        bool replyAux = aux && !mouseRepliesAsKeyboard;
        switch (byte) {
        case 0xff:
            if (aux && ++mouseResets == 1 && resendMouseReset) {
                reply(0xfe, replyAux); break;
            }
            reply(0xfa, replyAux);
            reply(badBAT ? 0xfc : 0xaa, replyAux, aux ? mouseBATms : keyboardBATms);
            if (aux) reply(0x00, replyAux, mouseBATms);
            break;
        case 0xf5: case 0xf6:
            reply(0xfa, replyAux); break;
        case 0xee:
            assert(!aux); reply(0xee, false); break;
        default:
            std::fprintf(stderr, "Unexpected device command %02x\n", byte);
            std::abort();
        }
    }
};

static Mock8042 *hardware;
static UInt8 inb(unsigned short port) {
    assert(port == 0x60 || port == 0x64);
    return port == 0x64 ? hardware->status() : hardware->data();
}
static void outb(unsigned short port, UInt8 byte) {
    assert(port == 0x60 || port == 0x64);
    if (port == 0x64) hardware->command(byte); else hardware->output(byte);
}
static void IODelay(unsigned int microseconds) { hardware->now += microseconds; }
static void IOSleep(unsigned int milliseconds) { hardware->now += UInt64(milliseconds) * 1000; }
static UInt32 VaioPS2NowMS(void) { return UInt32(hardware->now / 1000); }
static int IOLog(const char *, ...) { return 0; }

#include "../drivers/VAIOPS2Controller-r3-offline/VAIOPS2Init.h"

static VaioPS2InitResult run(Mock8042 &model) {
    hardware = &model;
    VaioPS2InitResult result;
    bool safe = VaioPS2ColdInit(&result);
    assert(safe == result.transportSafe);
    assert(model.now <= 20010000ULL);
    assert(model.writes < 200);
    return result;
}
static void finalPolicy(const Mock8042 &model) {
    assert((model.ctr & 0x73) == 0x40); // IRQs off, clocks on, translation on.
}
int main() {
    {
        Mock8042 model;
        VaioPS2InitResult r = run(model);
        assert(r.transportSafe && r.initialCTRValid && r.finalCTRValid);
        assert(r.keyboardReady && r.mouseReady && model.controlTests == 2);
        finalPolicy(model);
        std::puts("PASS normal devices and CONTROL reply routing");
    }
    {
        Mock8042 model;
        model.keyboardBATms = 1800;
        model.mouseBATms = 2500;
        VaioPS2InitResult r = run(model);
        assert(r.transportSafe && r.keyboardReady && r.mouseReady);
        assert(model.now >= 4300000ULL);
        finalPolicy(model);
        std::puts("PASS long device BAT deadlines");
    }
    {
        Mock8042 model;
        model.busy = true;
        VaioPS2InitResult r = run(model);
        assert(!r.transportSafe && !r.keyboardReady && !r.mouseReady);
        assert(model.writes == 0);
        std::puts("PASS busy controller stops without writing");
    }
    {
        Mock8042 model;
        model.silentControl = true;
        VaioPS2InitResult r = run(model);
        assert(!r.initialCTRValid && !r.keyboardReady && !r.mouseReady);
        assert(!r.transportSafe);
        std::puts("PASS missing CONTROL reply is not accepted as zero");
    }
    {
        Mock8042 model;
        model.silentKeyboard = true;
        VaioPS2InitResult r = run(model);
        assert(r.transportSafe && !r.keyboardReady && r.mouseReady);
        finalPolicy(model);
        std::puts("PASS keyboard failure does not suppress mouse initialization");
    }
    {
        Mock8042 model;
        model.silentMouse = true;
        VaioPS2InitResult r = run(model);
        assert(r.transportSafe && r.keyboardReady && !r.mouseReady);
        finalPolicy(model);
        std::puts("PASS mouse failure does not suppress keyboard initialization");
    }
    {
        Mock8042 model;
        model.badBAT = true;
        VaioPS2InitResult r = run(model);
        assert(!r.keyboardReady && !r.mouseReady);
        std::puts("PASS failed BAT is not accepted as initialized hardware");
    }
    {
        Mock8042 model;
        model.reply(0x08, true); model.reply(0x00, true); model.reply(0xaa, false);
        VaioPS2InitResult r = run(model);
        assert(r.transportSafe && r.keyboardReady && r.mouseReady);
        assert(r.discardedBytes >= 3);
        finalPolicy(model);
        std::puts("PASS stale pre-initialization bytes are drained");
    }
    {
        Mock8042 model;
        model.flood = true;
        VaioPS2InitResult r = run(model);
        assert(!r.transportSafe);
        std::puts("PASS endless output stream has a bounded failure");
    }
    {
        Mock8042 model;
        model.mouseRepliesAsKeyboard = true;
        VaioPS2InitResult r = run(model);
        assert(r.transportSafe && r.keyboardReady && !r.mouseReady);
        std::puts("PASS wrong-stream device replies are not accepted");
    }
    {
        Mock8042 model;
        model.resendMouseReset = true;
        VaioPS2InitResult r = run(model);
        assert(r.transportSafe && r.keyboardReady && r.mouseReady);
        assert(model.mouseResets == 2);
        std::puts("PASS mouse RESEND retries repeat D4 endpoint selection");
    }
}
