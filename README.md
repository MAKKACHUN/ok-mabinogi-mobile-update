<div align="center">
  <img src="icons/icon.png" alt="icon" width="200"><br>
  <h1>ok-mabinogi-mobile</h1>
  <p>一款基於圖像辨識的《瑪奇 Mobile》自動化工具。</p>
  <p>基於 <a href="https://github.com/ok-oldking/ok-script">ok-script</a> 框架開發。</p>

  <p>
    <img src="https://img.shields.io/badge/platform-Windows-blue" alt="平台">
    <img src="https://img.shields.io/badge/python-3.12-skyblue" alt="Python版本">
    <a href="https://github.com/MAKKACHUN/ok-mabinogi-mobile/releases"><img src="https://img.shields.io/github/downloads/MAKKACHUN/ok-mabinogi-mobile/total" alt="總下載量"></a>
    <a href="https://github.com/MAKKACHUN/ok-mabinogi-mobile/releases"><img src="https://img.shields.io/github/v/release/MAKKACHUN/ok-mabinogi-mobile" alt="最新版本"></a>
  </p>
</div>

## ⚠️ 免責聲明

本軟體為開源、免費的外部工具，僅供學習和交流使用，透過模擬操作與《瑪奇 Mobile》的使用者介面互動。

-   **運作原理**：程式僅透過辨識現有使用者介面與遊戲互動，不會修改任何遊戲檔案或程式碼。
-   **使用目的**：旨在為使用者提供便利，無意破壞遊戲平衡或提供任何不公平優勢。
-   **法律責任**：使用本軟體產生的一切問題及後果，均與本專案及開發團隊無關。開發團隊保留對本專案的最終解釋權。
-   **商業行為**：若您遇到商家使用本軟體提供代練服務並收費，此行為可能涉及裝置與時間成本，與本軟體本身無關。

> **使用第三方自動化工具可能違反遊戲服務條款，並可能導致帳號受限制或封禁。使用前請先了解並自行承擔所有風險。**

## ✨ 主要功能

*   **野外首領排程**
    *   管理及執行野外首領排程
*   **採集排程**
    *   建立採集佇列並自動執行
*   **狩獵場事件**
    *   按優先次序自動完成已選擇的狩獵場事件

## 🖥️ 執行環境與相容性

*   **作業系統**：Windows
*   **遊戲解析度**：1600x900 或更高（建議使用 16:9 長寬比）
*   **遊戲語言**：繁體中文

## 🚀 安裝指南

### 方式一：使用安裝程式（建議）

此方法適合大多數使用者，簡單快捷，並支援自動更新。

1.  前往 [**Releases**](https://github.com/MAKKACHUN/ok-mabinogi-mobile/releases) 頁面。
2.  下載最新、名稱以 `setup.exe` 結尾的安裝程式。
3.  按兩下執行安裝程式，依照提示完成安裝即可。

### 方式二：從原始碼執行（適合開發者）

此方法需要具備 Python 環境，適合希望進行二次開發或偵錯的使用者。

1.  **環境要求**：確保已安裝 **Python 3.12** 或更高版本。
2.  **複製儲存庫**：
    ```bash
    git clone https://github.com/MAKKACHUN/ok-mabinogi-mobile.git
    cd ok-mabinogi-mobile
    ```
3.  **安裝相依套件**：
    ```bash
    pip install -r requirements.txt --upgrade
    ```
    *提示：每次更新程式碼後，建議重新執行此命令，確保相依套件為最新版本。*
4.  **執行程式**：
    ```bash
    # 執行正式版
    python main.py

    # 執行偵錯版（會輸出更詳細的紀錄）
    python main_debug.py
    ```

## 📖 使用指南與常見問題

為確保程式穩定執行，請在使用前仔細閱讀以下設定要求和常見問題解答。

### 一、使用前設定（必讀）

啟動自動化前，請務必檢查並確認以下設定：

*   **圖形設定**
    *   **顯示卡濾鏡**：**關閉**所有顯示卡濾鏡和銳化效果（例如 NVIDIA Freestyle、AMD FidelityFX）。
    *   **遊戲亮度**：使用遊戲的**預設亮度**。
    *   **遊戲 UI 縮放**：使用遊戲的**預設 100% 縮放**。
*   **解析度**
    *   建議使用 **1600x900** 或以上的常見 16:9 解析度。
*   **按鍵設定**
    *   請務必使用遊戲的**預設按鍵綁定**。
*   **第三方軟體**
    *   關閉任何在遊戲畫面上顯示資訊的懸浮視窗，例如 MSI Afterburner（小飛機）的**幀率顯示**。
*   **視窗與系統狀態**
    *   **滑鼠干擾**：遊戲視窗位於**前景**時，請勿移動滑鼠，否則會干擾程式的模擬點擊。
    *   **視窗狀態**：遊戲視窗可以置於背景，但**不可最小化**。
    *   **系統狀態**：請勿讓電腦**關閉螢幕**或**鎖定畫面**，否則程式將會中斷。

### 二、快速上手

1.  進入您想要自動化的關卡或場景。
2.  在程式介面的「全自動」頁面，選擇要執行的功能並點擊「開始」。

### 三、常見問題解答（FAQ）

**Q1：角色移動時經常撞牆，或者無法準確到達目標位置？**

*   **原因**：遊戲引擎的移動速度與幀率（FPS）密切相關。
*   **解決方法**：
    1.  **調整遊戲幀率**：在遊戲設定中，依次嘗試將幀率上限設為 **60 FPS**、**120 FPS**及**無限制**，找出表現最穩定的設定。
    2.  **調整按鍵時長**：在對應任務的設定中微調**按鍵時長**參數。
    3.  **等待官方最佳化**：此問題可能需要等待遊戲官方後續更新修正。

### 四、問題回報

如果以上方法未能解決您的問題，歡迎透過 [**Issues**](https://github.com/MAKKACHUN/ok-mabinogi-mobile/issues) 回報。為協助我們快速定位問題，提交時請提供以下資訊：

*   **問題截圖**：清楚顯示異常畫面或錯誤提示。
*   **紀錄檔案**：附上程式目錄內的 `.log` 紀錄檔案。
*   **詳細描述**：您進行了哪些操作？問題的具體情況是甚麼？問題能否穩定重現，還是偶爾發生？
