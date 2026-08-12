# Gather Plugin

自動採集 Plugin，支援多種生活技能、採集排程、循環執行及 JSON 保存。

## 功能

- 多生活技能採集
- 動態資源下拉選單
- 新增排程
- 刪除排程
- 上移／下移
- 每項設定執行分鐘
- 每項設定每輪間隔
- 循環執行
- JSON 保存與自動載入

## 結構

```text
src/plugins/gather/
├─ data/
├─ dialogs/
├─ managers/
├─ models/
├─ pages/
├─ storage/
├─ tasks/
├─ plugin.py
└─ README.md

Task Entry
["src.plugins.gather.tasks.AutoGatherTask", "AutoGatherTask",]

JSON 設定
configs/gather_queue.json

新增生活技能
在 assets/coco_annotations.json 加入 Template。
在 data/gather_database.py 加入技能及資源設定。
不需要修改 AutoGatherTask、Dialog 或 Queue Manager。

注意
Template 名稱必須與 gather_database.py 內的 feature 完全一致。
遊戲更新 UI 後，可能需要重新標註 Template。
目前 Task 依賴專案共用的 BaseDNATask 及 DNAOneTimeTask。


---

## Step 5：確認 Plugin metadata

執行：

```powershell
python -c "from src.plugins.gather import PLUGIN_NAME, PLUGIN_VERSION, TASK_ENTRY; print(PLUGIN_NAME, PLUGIN_VERSION, TASK_ENTRY)"

預期：
自動採集 1.0.0 ['src.plugins.gather.tasks.AutoGatherTask', 'AutoGatherTask']