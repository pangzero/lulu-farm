# 性能记录原值

r06 had no binary Profiler; r07 captures include CPU Profiler and ten-second rotation flush overhead. Same M5, 1280x720, Desktop and 20 mature plots, but profiler overhead is not subtracted. D6 final route moves two west-house intermediate points 0.6m east to avoid the inherited fence endpoint; the 31 points and key stops remain, but this is not an identical-path A/B comparison. No causal or acceptance conclusion.

| 阶段 | 有效秒 | 圈 | 帧 | 均值 ms | P95 ms | 最大 ms | 二进制 Profiler |
|---|---:|---:|---:|---:|---:|---:|---|
| r06 baseline | 917.684 | 7 | 109241 | 8.3926 | 8.3672 | 1859.2706 | 关 |
| D5 | 912.723 | 7 | 102399 | 8.7010 | 8.5100 | 19762.5446 | 开 |
| D2 | 912.725 | 7 | 103695 | 8.8013 | 8.8560 | 19056.6597 | 开 |
| D3 | 312.691 | 2 | 36132 | 8.6539 | 9.0690 | 225.7145 | 开 |
| D4 | 912.739 | 8 | 105841 | 8.6175 | 8.9825 | 2658.1440 | 开 |
| D6 | 912.750 | 8 | 99359 | 9.1232 | 13.0045 | 5273.0780 | 开 |

只采集和列值；原因、预算和验收由 Opus 判断。Main Thread / Render Thread 不可用项不能当作 0ms；温度未测。
