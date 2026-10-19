# 第三方来源 / Third-party provenance

## ApplePS2Controller source

- Upstream: [Apple OSS Distributions / ApplePS2Controller](https://github.com/apple-oss-distributions/ApplePS2Controller)
- Version: `ApplePS2Controller-8`
- Pinned commit: `dcd0a6584cdba6cdc643281d57d22864cb85ee52`
- Included derivative: `drivers/VAIOPS2Controller-r3-offline/`
- Applicable upstream notice: Apple Public Source License 1.1
- Complete license: [APSL-1.1](licenses/APSL-1.1.txt)
- License text source: [Apple's DSLDAPPlugIn APPLE_LICENSE](https://github.com/apple-oss-distributions/DSLDAPPlugIn/blob/main/APPLE_LICENSE)
- Downloaded license SHA256: `359a21ed59e82096455398ea10c5bc8c3ff28e7acf7935b77751d70e3630fc95`

保留七个 Apple C++/头文件中的原版权声明。控制器源码/头文件及新增初始化辅助文件包含适用的修改声明；2026-10-19 的行为修改及本次仅涉及注释的归档调整，记录在该目录 `NOTICE` 中。R3 仍是不可部署的研究分支。

The seven inherited Apple C++/header files retain their original notices. The modified controller source/header and added initialization helper carry modification notices. The directory's `NOTICE` records the behavioral changes dated 2026-10-19 and this export's comment-only changes. R3 remains unsuitable for deployment.

## Reference material

The loader preflight is project code based on inspection of [Apple IOKitUser-297.10 kld_patch.c](https://github.com/apple-oss-distributions/IOKitUser/blob/IOKitUser-297.10/kext.subproj/kld_patch.c). That Apple implementation is linked as a reference, not copied into the preflight tool. Portable tests construct their own synthetic Mach-O data and include no original driver bytes.

Protocol references are listed in the driver `NOTICE`. Linux code and the IBM/Intel reference documents are not bundled. SDKs, compiler distributions, installation media and third-party driver binaries are also not bundled.

加载器预检依据 Apple 旧源码所描述的格式约束编写；便携测试使用自行构造的数据，不含原驱动字节。协议参考资料只保留来源链接，未打包 Linux 源码、IBM/Intel 文档、SDK、编译器或安装介质。

## Photograph

`github-ph.jpg` was supplied by the project owner as a photo of the physical VAIO running Tiger. Its exported copy removes capture EXIF/XMP/IPTC/comments while retaining the compressed image streams, color profile and technical HDR gainmap metadata. The MPF primary-image length was updated after metadata removal. The original photograph is unchanged in the local workspace. The image is not covered by the Apple source license.

照片由项目所有者提供。公开副本移除拍摄元数据，保留色彩及 HDR 技术信息，并更新相应的 MPF 图像长度；未重新编码、裁剪或改变图像像素，原图留在本地。Apple 源码许可证不涵盖这张照片。
