# Deye EW11 Home Assistant Integration

Custom integration to monitor **Deye Hybrid Inverters** via the **EW11 WiFi stick** (Modbus TCP).

## Features

- 🔌 **Stable Connection:** Optimized Modbus TCP with 1.2s timeout and auto-reconnect.
- 💾 **Smart Caching:** Prevents "Unavailable" during WiFi glitches by showing cached data.
- ⚡ **Accurate Sensors:** Precise battery voltage (52.64V), generator power, and more.
- 🔋 **Smart Battery Runtime:**
  - **Charging:** Shows "Time to Full".
  - **Discharging:** Shows "Time to Empty".
  - **Format:** "14 год 46 хв" or "45 хв" (auto-formats based on duration).
- ⚙️ **Configurable:** Update interval, caching, battery capacity via UI.

## Installation (HACS)

1. **HACS** -> **Integrations** -> **3 dots** -> **Custom repositories**.
2. Add URL: `https://github.com/YOUR_USERNAME/zotac-deye-monitor`
3. Category: **Integration** -> **Add**.
4. Find "Deye EW11" and install.
5. Restart Home Assistant.

## Manual Installation

1. Download `custom_components/deye_ew11` folder.
2. Copy to `config/custom_components/`.
3. Restart Home Assistant.

## Configuration

1. **Settings** -> **Devices & Services** -> **Add Integration** -> **Deye EW11**.
2. Enter:
   - **IP Address:** EW11 dongle IP (e.g., 192.168.1.103).
   - **Port:** 502 or 8899.
   - **Slave ID:** Usually 1.
   - **Battery Capacity:** Total kWh (for runtime calculation).

### Options

Click **Configure** to adjust:
- **Update Interval:** Data polling frequency (5-10s recommended).
- **Cache Data:** Smooth out connection drops.
- **Max Retries:** Failed updates before showing "Disconnected".

## Verified Models

- Deye SUN-5K-SG03LP1-EU
- Deye SUN-10K-SG04LP3-EU (and similar Hybrid models)

## Git Repository Setup

To upload this integration to GitHub:

```bash
cd D:\РОБОТА\Scripts\new_projects_bot\zotac-deye-monitor
git init
git add .
git commit -m "Initial release v1.0.1"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/zotac-deye-monitor.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.
