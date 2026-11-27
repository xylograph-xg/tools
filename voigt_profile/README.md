# Voigt 线形

[voigtReal(x, y)](src/voigt.ts) 计算 Faddeeva 函数在 x + iy 的实部，可用于高斯与洛伦兹展宽叠加的谱线。两个参数均为无量纲有限数，y ≥ 0。函数返回单个数值，没有默认参数、文件读写或参数校验。调用方负责检查输入。算法采用 Weideman (1994) 的 32 阶有理近似。

在本目录用 Node.js 24 计算中心值（约为 1）：

```sh
node --input-type=module -e "import {voigtReal} from './src/voigt.ts'; console.log(voigtReal(0, 0))"
```

[plot 的光谱分峰](../../plot/app/src/lib/spectrum.ts) 将自变量和洛伦兹半宽按高斯宽度缩放，再除以中心值以获得峰高归一的曲线。代码取自 plot 项目，沿用 [MIT 许可证](LICENSE)。
