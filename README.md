<p align="center">
  <a href="https://morphe.software/add-source?github=Rakastanyan/piko-newx">
    <img src="assets/add-to-morphe.svg" alt="Add to Morphe" height="48">
  </a>
</p>

Builds and publishes the [NewX](https://github.com/crimera/piko/tree/x-lite) patch bundle from the [Piko `x-lite` branch](https://github.com/crimera/piko/tree/x-lite), with built-in **Simplified & Traditional Chinese (繁简双语)** localization for NewX settings and patch options.

## 中文说明（繁简双语支持）

本仓库在构建 `.mpp` 补丁包时会自动注入多语言本地化资源：

1. **X 应用内 NewX 设置界面（繁简双语自动切换）**：
   - 自动向 `patches/src/main/resources/addresources/` 注入以下 Android 语言资源目录：
     - `locales/values-zh-rCN/newx/strings.xml`（简体中文）
     - `locales/values-zh-rTW/newx/strings.xml`（繁體中文·台灣）
     - `locales/values-zh-rHK/newx/strings.xml`（繁體中文·香港）
   - 应用安装后将根据手机系统语言自动显示对应的简体中文或繁体中文界面；若上游新增词条，构建脚本 `localize.py` 会自动以英文原文作为回退保留。

2. **Morphe 补丁选项与描述本地化**：
   - 由 `locales/patches_i18n.json` 与 `localize.py` 提供补丁名称、描述及选项（如 `Package name`、`App name` 等）的繁简双语翻译。
   - 支持通过 `--patch-locale` 参数或环境变量 `PIKO_PATCH_LOCALE` 指定输出模式：
     - `bilingual`（默认）：繁简双语对照显示
     - `zh-rCN`：纯简体中文
     - `zh-rTW`：纯繁体中文
     - `en`：保留原版英文

# Credits
- [morphe](https://github.com/MorpheApp) - patcher
- [revanced](https://github.com/ReVanced) - previous patcher
- [j-hc](https://github.com/j-hc) - Project is inspired by j-hc's revanced builder template.
