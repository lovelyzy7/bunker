# bunker/web/signing —— 签名 key 已对齐到 mod 菜单 JP key

> 本目录原有 3 个文件（`bunker-key.pem` / `bunker-cert.der` / `bunker-key.p12`）
> 在 2026-10-25 的任务 I（JP APK 构建+签名）中被**替换为 mod 菜单 JP key**
> （`NieR-Re-In-Carnation-Mod_Menu/jp-client/keys/nier-jp.keystore`）。
> 原始 key 材料已备份到：
> `E:\NieRReincarnation\zh-l10n\work\apk\backup\bunker-web-signing-original\`
> （原证书 SHA-256 `B2:57:2B:FA:…:2F:F9`）。

## 新 key（= mod 菜单 / lunar-scripts-jp key）

| 项 | 值 |
|---|---|
| 来源 | `E:\NieRReincarnation\NieR-Re-In-Carnation-Mod_Menu\jp-client\keys\nier-jp.keystore`（JKS） |
| 同一文件 | `E:\NieRReincarnation\lunar-scripts-jp\keys\nier-jp.keystore`（sha256 `4C5CF2D4…6346F8`，逐字节相同） |
| alias | `nier` |
| store/key 密码 | `lunar-jp` |
| 证书 SHA-256 | `EE:C2:3B:E0:CB:20:5C:40:17:91:BE:3D:4B:82:E8:85:15:60:F5:C2:AE:D3:EC:64:41:66:09:3D:3D:98:A2:FE` |
| 证书 DN | `CN=lunar-scripts-jp, OU=private-server, O=local, L=NA, ST=NA, C=JP` |
| key 格式 | RSA 2048，导出为 PKCS#8 PEM（`BEGIN PRIVATE KEY`）+ X.509 DER 证书 |

## 文件对应关系

| 文件 | 内容 | 用途 |
|---|---|---|
| `bunker-key.pem` | PKCS#8 PEM 私钥 | `android/tools/apk_sign.py` 默认读取 |
| `bunker-cert.der` | X.509 DER 证书（与 keystore 内证书同一份） | `apk_sign.py` 默认读取；apksigner 显示指纹依据 |
| `bunker-key.p12` | PKCS12（alias `nier` / 密码 `lunar-jp`） | 网页发布包里给用户下载（`web/build_site.py` 会拷贝到站点根） |

> `apk_sign.py` 代码本身不读 `.p12`（它读 PEM+DER）；`.p12` 是公开下载件，
> 保持同一把 key 以便用户用同一 key 手动签名/覆盖安装。

## 重新生成（可复现）

```powershell
# 1) JKS -> PKCS12（用 JDK 的 keytool）
keytool -importkeystore -srckeystore nier-jp.keystore -srcstoretype JKS `
  -srcstorepass lunar-jp -srcalias nier `
  -destkeystore bunker-key.p12 -deststoretype PKCS12 `
  -deststorepass lunar-jp -destkeypass lunar-jp -noprompt
# 2) PKCS12 -> PEM 私钥 + DER 证书（用 JDK KeyStore API 导出；见
#    zh-l10n/work/apk/bunker-key/ExportKey.java 与 align_bunker_key.py）
java -cp <classes> ExportKey bunker-key.p12 lunar-jp nier bunker-key.pem bunker-cert.der
```

完整脚本：`E:\NieRReincarnation\zh-l10n\work\apk\align_bunker_key.py`
（备份原 key → 导出 → 替换 → 用 `apk_sign.py` 真签一个 APK → apksigner 验证指纹）。

## 注意（本任务未改的文件）

- `web/index.html`（下载提示文案）与根 `README.md` 仍写着旧口令/别名
  （`bunker-key.p12` / password and alias `bunker`）——它们不在本任务写范围内，
  需要后续同步为：**alias `nier`，密码 `lunar-jp`**。`web/build_site.py` 只按文件名
  拷贝 pem/der/p12，不校验内容，所以站点构建本身不受影响。
- `android/tools/package_game.py` 的桌面端 `scripts/build.py` 签名路径硬编码
  alias `lunar-local` / 密码 `android`（用于 bunker 自身 companion APK）；
  本任务只对齐 **web/apk_sign.py + web/signing key**。若要让桌面端 bunker 构建也用
  mod 菜单 key，需要给 `package_game.py`/`scripts/build.py` 增加 alias/pass 参数
  （属于后续改动，本目录未改）。
