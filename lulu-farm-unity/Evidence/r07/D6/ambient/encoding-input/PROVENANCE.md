编码输入：帧 PNG 与原记录硬链接，帧索引逐字节复制；recording.json 是运行时在 StopRecording 后实际抓取的 recording-stop-snapshot.json，未改数值。旧录制器在命令行退出又重写 elapsedSeconds，原始退出清单仍保留在原目录，因此编码选用先前实测停止清单，避免额外静帧尾段。
来源：Evidence/r07/D6/ambient/20261024-023412-455/walkthrough-023416-025
