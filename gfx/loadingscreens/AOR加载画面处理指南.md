# AOR 加载画面处理指南（可独立复现）

本文件可以单独放在 `gfx/loadingscreens` 并随模组提交到 GitHub。**下方包含完整的单文件转换程序** 后续 AI 应先检查仓库当前状态与适用的 AGENTS.md，再执行修改。

## 一、必须遵守的要求

1. **所有加载图片和开始界面背景都必须转换为真正的黑白灰度图。** 不能保留黄色、绿色、棕褐色等色调。每个输出像素必须满足 `R = G = B`，Alpha 为 255。
2. **禁止生成式 AI 重绘、扩图、补画、修复或重新生成照片。** 只能使用普通的方向校正、等比例缩放、裁切、灰度转换和亮度遮罩；不得改变人物、建筑等画面内容。
3. 输出固定为 **1920×1440，DDS，8.8.8.8 BGRA，32 BPP，未压缩，无 mipmap**。不得改为 DXT1/DXT5、BC1/BC3、RGB 24 位等格式。
4. 不拉伸、不补边。按覆盖目标画布的比例缩放，居中裁切；应目视确认重要人物没有被切掉。需要改变裁切中心时，另行记录。
5. 加载图采用柔和暗角和底部渐黑；名言由游戏另行显示在左下角。不要给图片加硬边矩形黑条，不要把名言或作者烘焙进图片。
6. 不得对已经加过暗角的成品 DDS 重复应用暗角，避免越来越黑。重新制作必须使用未处理的原图。

## 二、文件分别控制什么

以下路径均相对于模组根目录，不依赖电脑用户名或安装盘符。

| 文件 | 职责 |
|---|---|
| `gfx/loadingscreens/load_1.dds`～`load_15.dds` | 当前 15 张加载照片，已经处理过暗角与底部渐黑；以后新增前应重新清点编号 |
| `gfx/loadingscreens/loading_screen_border_small.dds` | 界面装饰边框，不是第 16 张轮播照片；不要把它也当作照片处理 |
| `gfx/MAIN_MENU.dds` | 开始界面的背景；当前使用文件名为“倍倍尔在演讲.png”的照片 |
| `interface/frontendmainviewbg.gfx` | `GFX_frontend_bg` 指向 `gfx/MAIN_MENU.dds` |
| `interface/frontendmainview.gui` | 主菜单屏幕适配及按钮；通常替换 MAIN_MENU.dds 即可，不用改它 |
| `interface/load_screen.gui` | 加载状态隐藏、名言位置与对齐 |
| `interface/load_screen_font.gfx` | 名言字体 `loadscreen_tip` 的定义 |
| `gfx/fonts/aor_loading_huiwen/` | 加载名言专用的 40 号汇文明朝体，行高 48；游戏需要，不能删除 |
| `gfx/fonts/huiwenminchao/` | 原有地图使用的 80 号汇文明朝体，不能删除 |

名言布局：`tip` 锚点 `LOWER_LEFT`，文本位置 `(80,-244)`、宽 1400、高 216、左对齐、垂直居中。`status` 窗口在 `(-100000,-100000)`，保留控件但不显示。作者颜色沿用原文本的颜色标记，不影响背景照片必须为黑白的要求。

## 三、工作流程

1. 清点加载目录，确认新图身份、构图与最大编号；不要覆盖已有照片。当前下一张为 `load_16.dds`，但操作前必须重新检查。
2. 将要覆盖的 DDS、文档或界面配置先备份到加载目录之外；不要把旧 DDS 副本留在加载目录里参与轮播。
3. 将下方唯一的 PowerShell 代码块保存为 `Convert-AorLoadingImage.ps1`。它是完整程序，不需要任何配套 `.cs` 文件。可以放在临时目录；不要求提交到仓库。
4. 在 Windows + PowerShell 7 中运行。输入未处理的 JPG/PNG/BMP/TIFF，输出先放临时目录。Loading 模式执行黑白转换、暗角和底部渐黑；Menu 模式只进行方向校正、缩放裁切和黑白转换，不加加载画面的渐黑效果。
5. 检查成品预览：重要人物没有被裁切、没有色调、下方名言位置足够暗。脚本还会自动逐像素确认 `R=G=B`、Alpha=255，并验证 DDS 头和文件大小。
6. 确认后将新照片命名为 `load_N.dds` 放入加载目录。保留既有界面和字体设置。安装后比较源成品与目标文件的 SHA-256。
7. 模组内 `descriptor.mod` 与本地启动器使用的上一级 `.mod` 文件都应包含 `replace_path="gfx/loadingscreens"`，以排除原版/DLC加载图；GitHub 下载者需要按自己的安装路径配置本地启动器，不能直接沿用他人的绝对路径。
8. 新增轮播图片不需要逐张注册 sprite。不要为加载轮播随意填写 `common/frontend/backgrounds/base_backgrounds.txt`，它控制主菜单背景选择，与当前固定 MAIN_MENU 背景及加载图片不是同一用途。
9. 启用该模组并重启游戏验证加载轮播和主菜单。只验证文件/预览时，明确写出“尚未进游戏实测”，不要保证运行时表现已验证。

示例命令（在自己选择的临时目录操作，替换路径）：

```text
pwsh -NoProfile -File ./Convert-AorLoadingImage.ps1 -Source ./新照片.png -Destination ./load_16.dds -Mode Loading
pwsh -NoProfile -File ./Convert-AorLoadingImage.ps1 -Source ./倍倍尔在演讲.png -Destination ./MAIN_MENU.dds -Mode Menu
```

脚本默认不覆盖现有输出；备份后才可显式加 `-Force`。输入 DDS 会被拒绝，以免把成品重复加暗角。它不会删除原图、修改系统字体、更新模组配置或自动选择编号。

## 四、完整可执行代码

以下代码块必须完整复制。只依赖 Windows、PowerShell 7 和 System.Drawing；不依赖 Python、ImageMagick、AI 绘图、联网或本项目 tools 中的任何文件。

<!-- AOR_STANDALONE_SCRIPT_BEGIN -->

```powershell
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$Source,
 [Parameter(Mandatory=$true)][string]$Destination,
 [ValidateSet('Loading','Menu')][string]$Mode='Loading',
 [switch]$Force
)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
if(-not ('AorLoadingWriter' -as [type])){
 $code=@'
using System;
using System.IO;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
public static class AorLoadingWriter {
 static double S(double a,double b,double v){double t=Math.Max(0,Math.Min(1,(v-a)/(b-a)));return t*t*(3-2*t);}
 public static void ProcessAndSave(Bitmap bmp,string path,bool loading){
  int w=bmp.Width,h=bmp.Height;byte[] p=new byte[w*h*4];
  var d=bmp.LockBits(new Rectangle(0,0,w,h),ImageLockMode.ReadOnly,PixelFormat.Format32bppArgb);
  try{for(int y=0;y<h;y++)Marshal.Copy(IntPtr.Add(d.Scan0,y*d.Stride),p,y*w*4,w*4);}finally{bmp.UnlockBits(d);}
  for(int y=0;y<h;y++){
   double fy=(double)y/(h-1),ny=(fy-.45)/.62;
   double bottom=.998*Math.Pow(S(.63,.985,fy),1.30),top=.18*(1-S(0,.22,fy));
   for(int x=0;x<w;x++){
    int i=(y*w+x)*4;
    // Mandatory monochrome: one rounded luminance value for all RGB channels.
    double gray=Math.Round(.299*p[i+2]+.587*p[i+1]+.114*p[i]);
    double k=1;
    if(loading){double nx=(double)x/(w-1)*2-1;double r=Math.Sqrt(nx*nx*.81+ny*ny*.64);k=(1-.72*S(.40,1.13,r))*(1-bottom)*(1-top)*(1-.30*Math.Pow(Math.Abs(nx),8));}
    byte v=(byte)Math.Max(0,Math.Min(255,Math.Round(gray*k)));
    p[i]=p[i+1]=p[i+2]=v;p[i+3]=255;
   }
  }
  using(var bw=new BinaryWriter(File.Create(path))){
   bw.Write(System.Text.Encoding.ASCII.GetBytes("DDS "));
   foreach(uint v in new uint[]{124,0x100f,(uint)h,(uint)w,(uint)(w*4),0,0})bw.Write(v);
   for(int i=0;i<11;i++)bw.Write(0);
   foreach(uint v in new uint[]{32,0x41,0,32,0xff0000,0xff00,0xff,0xff000000,0x1000,0,0,0,0})bw.Write(v);
   bw.Write(p);
  }
  Validate(path);
 }
 public static long CountColored(string path){
  byte[] b=File.ReadAllBytes(path);long count=0;
  for(int i=128;i<b.Length;i+=4)if(b[i]!=b[i+1]||b[i]!=b[i+2])count++;
  return count;
 }
 public static void Validate(string path){
  byte[] b=File.ReadAllBytes(path);
  if(b.Length!=11059328||System.Text.Encoding.ASCII.GetString(b,0,4)!="DDS ")throw new Exception("Invalid DDS size/magic");
  int[] offsets={4,8,12,16,20,28,76,80,84,88,92,96,100,104,108};
  uint[] expected={124,0x100f,1440,1920,7680,0,32,0x41,0,32,0xff0000,0xff00,0xff,0xff000000,0x1000};
  for(int j=0;j<offsets.Length;j++)if(BitConverter.ToUInt32(b,offsets[j])!=expected[j])throw new Exception("Invalid DDS header at "+offsets[j]);
  for(int i=128;i<b.Length;i+=4)if(b[i]!=b[i+1]||b[i]!=b[i+2]||b[i+3]!=255)throw new Exception("Image is not fully opaque monochrome");
 }
}
'@
 Add-Type -TypeDefinition $code -ReferencedAssemblies @([Drawing.Bitmap].Assembly.Location,[Drawing.Rectangle].Assembly.Location,[Runtime.InteropServices.Marshal].Assembly.Location)
}
$sourcePath=(Resolve-Path -LiteralPath $Source).Path
$destinationPath=[IO.Path]::GetFullPath($Destination)
if([IO.Path]::GetExtension($sourcePath).ToLowerInvariant() -notin @('.jpg','.jpeg','.png','.bmp','.tif','.tiff')){throw 'Input must be an original JPG/PNG/BMP/TIFF, not a processed DDS.'}
if([IO.Path]::GetExtension($destinationPath).ToLowerInvariant() -ne '.dds'){throw 'Destination must end in .dds'}
if((Test-Path -LiteralPath $destinationPath) -and -not $Force){throw 'Back up existing output before explicitly using -Force.'}
[IO.Directory]::CreateDirectory((Split-Path $destinationPath -Parent))|Out-Null
$image=[Drawing.Image]::FromFile($sourcePath);$bitmap=$null;$g=$null
try{
 if($image.PropertyIdList -contains 274){$o=[BitConverter]::ToUInt16($image.GetPropertyItem(274).Value,0);$r=switch($o){2{4}3{2}4{6}5{5}6{1}7{7}8{3}default{0}};$image.RotateFlip([Drawing.RotateFlipType]$r)}
 $bitmap=[Drawing.Bitmap]::new(1920,1440,[Drawing.Imaging.PixelFormat]::Format32bppArgb)
 $g=[Drawing.Graphics]::FromImage($bitmap)
 $g.CompositingMode=[Drawing.Drawing2D.CompositingMode]::SourceCopy
 $g.CompositingQuality=[Drawing.Drawing2D.CompositingQuality]::HighQuality
 $g.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
 $g.PixelOffsetMode=[Drawing.Drawing2D.PixelOffsetMode]::HighQuality
 $scale=[Math]::Max(1920.0/$image.Width,1440.0/$image.Height)
 $cw=1920/$scale;$ch=1440/$scale;$cx=($image.Width-$cw)/2;$cy=($image.Height-$ch)/2
 $attributes=[Drawing.Imaging.ImageAttributes]::new()
 try{$attributes.SetWrapMode([Drawing.Drawing2D.WrapMode]::TileFlipXY);$g.DrawImage($image,[Drawing.Rectangle]::new(0,0,1920,1440),[single]$cx,[single]$cy,[single]$cw,[single]$ch,[Drawing.GraphicsUnit]::Pixel,$attributes)}finally{$attributes.Dispose()}
 $g.Dispose();$g=$null
 [AorLoadingWriter]::ProcessAndSave($bitmap,$destinationPath,($Mode -eq 'Loading'))
}finally{if($g){$g.Dispose()};if($bitmap){$bitmap.Dispose()};$image.Dispose()}
Write-Output "Verified monochrome $Mode DDS: $destinationPath"

```
<!-- AOR_STANDALONE_SCRIPT_END -->

## 五、复现参数与验收

图像处理顺序：EXIF 方向校正 → 等比例覆盖并居中裁切到 1920×1440 → 灰度 → Loading 模式额外叠加亮度遮罩 → 写 DDS。

灰度公式为 `round(0.299R + 0.587G + 0.114B)`，将同一个结果赋给 R、G、B。它不是“降低饱和度一点”，也不是“调成旧照片褐色”。

裁切：`s=max(1920/W,1440/H)`，源裁切宽高为 `1920/s,1440/s`，源裁切左上角为 `((W-1920/s)/2,(H-1440/s)/2)`；采用高质量双三次缩放。

遮罩的精确实现已完整包含在上述代码的 `ProcessAndSave`：平滑函数 `S(a,b,v)=t²(3-2t)`，其中 `t=clamp((v-a)/(b-a),0,1)`；底部渐黑从高度比例 0.63 开始，在 0.985 接近全黑，强度 0.998、指数 1.30；椭圆暗角强度 0.72，另有顶部和侧边柔和压暗。它只降低像素亮度，不生成新内容，不改变色相。

DDS 验收：

- 魔数为 `DDS `，传统 124 字节 DDS_HEADER，总文件头 128 字节。
- 宽 1920，高 1440，Pitch 7680，无 mipmap。
- 像素格式标志 `0x41`，FourCC=0，32 BPP。
- 掩码：R=`0x00FF0000`、G=`0x0000FF00`、B=`0x000000FF`、A=`0xFF000000`。
- 像素内存字节顺序为 **B、G、R、A**；Alpha=255；每个像素 R=G=B。
- 文件大小恰好为 **11,059,328 字节**（128 + 1920×1440×4）。
- 不包含名言、作者、Logo 或预览图标签，这些都不应烘焙进新加载照片。

为避免误解，DDS 的 BGRA 顺序仍然需要遵守，即使黑白图的三个颜色通道数值相同。



## 追加说明：主菜单同样需要暗角和底部渐黑

本节为追加内容，上文文字和代码原样保留。用户要求后续更新本指南时**只在末尾追加，不改写已有文字和代码**。

- 开始界面背景也必须带柔和暗角和底部渐黑，与加载图片统一，不能只做裁切和黑白转换。
- `gfx/MAIN_MENU.dds` 当前与 `gfx/loadingscreens/load_12.dds` 使用同一张已经处理过的倍倍尔演讲照片，两者文件内容相同。
- 保持 1920×1440、黑白（每像素 R=G=B）、BGRA 8.8.8.8、32BPP、未压缩 DDS；不得使用生成式 AI 重绘。
- 上文关于“Menu 模式不加渐黑”的文字和旧代码现作为原文保留；实际制作主菜单时，以本节的新要求为准。

若主菜单继续使用现有的倍倍尔演讲照片，备份原 MAIN_MENU.dds 后，直接复制已经带暗角的 `load_12.dds` 为 `gfx/MAIN_MENU.dds` 即可。**不要再对这张成品叠加一次暗角。**

若以后从新原图重做主菜单：从上文提取完整脚本到临时 `.ps1` 文件，再仅在该临时脚本中，把调用

```powershell
[AorLoadingWriter]::ProcessAndSave($bitmap,$destinationPath,($Mode -eq 'Loading'))
```

改成

```powershell
[AorLoadingWriter]::ProcessAndSave($bitmap,$destinationPath,$true)
```

这样 Menu 和 Loading 两种模式都会执行黑白转换、暗角及底部渐黑。不要为了修改临时脚本而编辑本指南前面的代码块。主菜单替换后需要重启游戏查看；文件校验通过不等于已经完成游戏内实测。
