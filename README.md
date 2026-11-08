<div align="center">
  <img src="https://raw.githubusercontent.com/byrsapty/zotac-deye-monitor/main/custom_components/deye_ew11/brand/icon@2x.png" alt="Deye EW11 Logo" width="200"/>
  <h1>Deye EW11 - Home Assistant Integration</h1>
</div>

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/byrsapty/zotac-deye-monitor.svg)](https://github.com/byrsapty/zotac-deye-monitor/releases)
[![License](https://img.shields.io/github/license/byrsapty/zotac-deye-monitor.svg)](https://github.com/byrsapty/zotac-deye-monitor/blob/main/LICENSE)

Інтеграція для моніторингу **гібридних інверторів Deye** через **WiFi донгл EW11**.
Підтримує **Modbus TCP** (пряме підключення) та **MQTT** (через брокер) протоколи.

> [!NOTE]
> ## 🆕 Що нового у 2.3
>
> - 🕒 **Графік відключень у панелі** (опційно). Якщо встановлена інтеграція [Svitlo.live](https://github.com/chaichuk/svitlo_live), під схемою показується наступне відключення з відліком часу, години без світла сьогодні/завтра і смужка графіка на 24 години. Вмикається одним рядком `outage:` у картці (див. пресет нижче).
> - ✏️ Візуальний редактор: окремий розділ «Графік відключень (Svitlo.live)» з вибором лише сенсорів Svitlo, короткі підписи полів з поясненнями під ними (довгі тексти більше не налазять на значення).
>
> ### 2.2.0
>
> - 🖥️ **Вбудована панель потоків енергії [ZOTAC Energy Flow Card](https://github.com/byrsapty/zotac-deye-monitor/blob/main/docs/energy-flow-card.md).** Картка тепер входить в інтеграцію і підключається на всіх дашбордах автоматично: копіювати файл у `/config/www/` і додавати ресурс вручну більше не потрібно. Готовий пресет для Deye SUN-6K у розділі «Панель потоків енергії» нижче.
> - 🛠️ **MQTT стабільніший** (з 2.1.1): виправлено втрату відповідей від EW11 (помилки «Timeout waiting for Block 2»), відкидаються запізнілі відповіді від попереднього блоку, один повтор запиту перед попередженням.
> - 🎨 Власні іконки інтеграції в папці `brand/` (HA 2026.3+).
> - ⚠️ Мінімальна версія Home Assistant тепер **2024.7**.

---

## ✨ Особливості

- 🔌 **Два протоколи підключення:**
  - **Modbus TCP** - пряме підключення до EW11
  - **MQTT** - через брокер (Mosquitto) для більш стабільної роботи
- 💾 **Розумне кешування:** При короткочасних збоях WiFi показує останні успішні дані замість "Unavailable"
- ⚡ **Точні дані:** Напруга батареї з точністю до сотих (52.64V), потужність генератора
- 🔋 **Розумний розрахунок часу роботи:**
  - **При зарядці:** Показує час до повного заряду
  - **При розрядці:** Показує час до повного розряду
  - **Формат:** Автоматично "14 год 46 хв" або "45 хв"
- ⚙️ **Налаштування через UI:** Вибір протоколу, інтервал оновлення, кешування, ємність батареї
- 🌍 **Мультимовність:** Повна підтримка української та англійської мов

---

## 📊 Сенсори (24+)

### 🔋 Батарея
- **SOC** (%, точний відсоток заряду)
- **Напруга** (V, з точністю 0.01V)
- **Струм** (A)
- **Потужність** (W, + заряд, - розряд)
- **Температура** (°C)
- **Час роботи** (розумний формат "X год Y хв")
- **Залишок енергії** (kWh)

### ☀️ Сонячні панелі (PV)
- **Потужність PV1/PV2** (W)
- **Напруга PV1/PV2** (V)
- **Струм PV1/PV2** (A)
- **Загальна потужність PV** (W)

### 🏠 Навантаження та мережа
- **Потужність навантаження** (W)
- **Потужність мережі** (W, + споживання, - віддача)
- **Напруга мережі** (V)
- **Частота мережі** (Hz)

### ⚙️ Генератор
- **Потужність генератора** (W)
- **Статус генератора** (Running/Stopped)

### 📈 Денна статистика
- День: Заряд батареї (kWh)
- День: Розряд батареї (kWh)
- День: Імпорт з мережі (kWh)
- День: Експорт в мережу (kWh)
- День: Споживання будинку (kWh)
- День: Вироблено PV (kWh)

---

## 🖥️ Панель потоків енергії

Разом з інтеграцією встановлюється картка **ZOTAC Energy Flow**: генератор, мережа й сонце зліва, шина інвертора по центру, дім і АКБ справа. Шина забарвлюється тим джерелом, що реально живить будинок, а при відсутності світла картка показує «Світла немає».

Додати: режим «Змінити» → **Додати картку** → **ZOTAC Energy Flow** (або «Ручна» і вставити YAML нижче). Усі параметри описані в [документації картки](https://github.com/byrsapty/zotac-deye-monitor/blob/main/docs/energy-flow-card.md).

### Пресет для Deye SUN-6K (АКБ 16 кВт·год)

Назви сенсорів `sensor.deye_sun_6k_*` відповідають пристрою з назвою **Deye SUN 6K**. Якщо ваш пристрій названо інакше, замініть префікс (знайти точні назви можна в Налаштування → Пристрої → ваш інвертор). Ємність АКБ (`battery_capacity_kwh`) і потужність інвертора (`inverter_power`) вкажіть свої.

```yaml
type: custom:zotac-energy-flow-card
entities:
  load: sensor.deye_sun_6k_load_power
  battery: sensor.deye_sun_6k_battery_power
  soc: sensor.deye_sun_6k_battery_soc
  battery_runtime: sensor.deye_sun_6k_battery_runtime
  grid: sensor.deye_sun_6k_grid_power
  grid_voltage: sensor.deye_sun_6k_grid_voltage
  grid_frequency: sensor.deye_sun_6k_grid_frequency
  generator: sensor.deye_sun_6k_generator_power
  generator_status: sensor.deye_sun_6k_generator_status
  pv: sensor.deye_sun_6k_pv_power
  inverter_temp: sensor.deye_sun_6k_dc_temperature
  # Графік відключень, якщо встановлено Svitlo.live (замініть на сенсор своєї черги)
  outage: sensor.svitlo_kyiv_1_1_electricity
battery_capacity_kwh: 16
battery_min_soc: 10
hide_when_zero:
  - pv
extras:
  - name: Струм AC
    entity: sensor.deye_sun_6k_inverter_current
    unit: A
  - name: DC Temp
    entity: sensor.deye_sun_6k_dc_temperature
    unit: °C
    warn_above: 65
  - name: AC Temp
    entity: sensor.deye_sun_6k_ac_temperature
    unit: °C
    warn_above: 60
  - name: АКБ вольти
    entity: sensor.deye_sun_6k_battery_voltage
    unit: V
    decimals: 2
  - name: АКБ ампери
    entity: sensor.deye_sun_6k_battery_current
    unit: A
  - name: АКБ Temp
    entity: sensor.deye_sun_6k_battery_temp
    unit: °C
    warn_above: 45
grid_options:
  columns: full
battery_invert: false
grid_invert: false
battery_marks: false
battery_level_colors: true
show_bus: true
bus_cycle: true
bus_label: true
show_inverter_temp: false
animations:
  - battery
  - bus
bus_mode: sources
inverter_power: 6000
flow_style: arrows
bypass_current_a: 40
bypass_badge: inverter
flow_fps: 30
flow_speed: 2
numbers_fps: 30
```

> Блок «Сонце» ховається, поки PV видає 0 Вт (`hide_when_zero: [pv]`). Якщо панелей немає, рядок `pv:` можна видалити.
>
> Рядок `outage:` потрібен лише з інтеграцією [Svitlo.live](https://github.com/chaichuk/svitlo_live): вкажіть її сенсор `…_electricity` для своєї черги (Налаштування → Пристрої → Svitlo). Без Svitlo.live видаліть цей рядок.

---

## 📦 Встановлення

### Спосіб 1: Через HACS (Рекомендовано)

1. Відкрийте **HACS** в Home Assistant
2. Перейдіть в розділ **Integrations**
3. Натисніть **три крапки (⋮)** → **Custom repositories**
4. Додайте репозиторій:
   ```
   https://github.com/byrsapty/zotac-deye-monitor
   ```
5. **Category:** `Integration`
6. Натисніть **ADD**
7. Знайдіть **Deye EW11 Inverter** в списку та натисніть **DOWNLOAD**
8. **Перезапустіть Home Assistant**

### Спосіб 2: Вручну

1. Завантажте [останню версію](https://github.com/byrsapty/zotac-deye-monitor/releases)
2. Розпакуйте архів
3. Скопіюйте папку `custom_components/deye_ew11` в:
   ```
   /config/custom_components/deye_ew11
   ```
4. Перезапустіть Home Assistant

---

## ⚙️ Налаштування

### Перше підключення

1. Перейдіть: **Settings** → **Devices & Services**
2. Натисніть **+ ADD INTEGRATION**
3. Знайдіть **Deye EW11**
4. Введіть параметри:

   | Параметр | Значення | Примітка |
   |----------|----------|----------|
   | **IP адреса** | `192.168.1.103` | IP вашого EW11 донгла |
   | **Порт** | `502` або `8899` | Зазвичай 502 для Modbus TCP |
   | **Slave ID** | `1` | Зазвичай 1 для Deye |
   | **Ємність батареї** | `10.24` | Загальна ємність в kWh |
   | **Інтервал оновлення** | `5` | Секунди (рекомендовано 5-10) |

5. Натисніть **SUBMIT**

### Додаткові налаштування

Після додавання інтеграції ви можете змінити параметри:

1. Перейдіть в **Settings** → **Devices & Services** → **Deye EW11**
2. Натисніть **CONFIGURE**
3. Доступні опції:
   - **Інтервал оновлення:** Як часто запитувати дані (1-60 сек)
   - **Увімкнути кешування:** Показувати старі дані при збоях
   - **Макс. спроб:** Скільки разів пробувати перед показом "Disconnected"

---

## 🔌 Протоколи підключення

Інтеграція підтримує **два протоколи** для роботи з EW11. Виберіть той, що вам підходить:

### 📡 Modbus TCP (Рекомендовано для початківців)

**Переваги:**
- ✅ Просте налаштування - тільки IP адреса
- ✅ Не потребує додаткового ПЗ
- ✅ Пряме підключення до EW11

**Налаштування:**
1. Виберіть протокол: **Modbus TCP**
2. Введіть:
   - IP адреса EW11
   - Порт (зазвичай 502)
   - Slave ID (зазвичай 1)

**Коли використовувати:**
- Локальна мережа з хорошим WiFi
- Перше підключення
- Не потрібна висока стабільність

---

### 📨 MQTT (Для досвідчених користувачів)

**Переваги:**
- ✅ Більш стабільна робота
- ✅ Менше timeout помилок
- ✅ Можливість віддаленого доступу

**Недоліки:**
- ❌ Потребує встановлення Mosquitto broker
- ❌ Складніше налаштування EW11

**Вимоги:**
1. **MQTT Broker:** (Mosquitto)
   ```bash
   # Ubuntu/Debian
   sudo apt-get install mosquitto
   ```
2. **Інтеграція "MQTT" в Home Assistant:**
   - Перейдіть в **Settings** → **Devices & Services**
   - Натисніть **+ ADD INTEGRATION**
   - Знайдіть **MQTT** і налаштуйте підключення до вашого брокера (Mosquitto)

**Встановлення paho-mqtt (для Home Assistant):**

Home Assistant потребує бібліотеку `paho-mqtt` для MQTT протоколу:

```bash
# Увійти в контейнер Home Assistant
docker exec -it homeassistant /bin/bash

# Встановити paho-mqtt
pip install paho-mqtt

# Вийти
exit

# Перезапустити Home Assistant
```

Або якщо використовуєте Home Assistant Core (не Docker):
```bash
pip install paho-mqtt
```

**Налаштування Mosquitto (додати користувача):**

Якщо використовуєте Mosquitto addon в Home Assistant:
1. Settings → Add-ons → Mosquitto broker → Configuration
2. Додайте користувача в секцію `logins`:
```yaml
logins:
  - username: mqtt_user
    password: mqtt_password_123
```
3. Save → Restart addon

**Налаштування EW11:**
1. Відкрийте веб-інтерфейс EW11: `http://<IP_EW11>`
2. Виберіть режим: **MQTT Client**
3. Налаштуйте:
   - Server IP: IP вашого ПК з Mosquitto (наприклад `192.168.1.155`)
   - Server Port: `1883`
   - **MQTT Account:** `mqtt_user`
   - **MQTT Password:** `mqtt_password_123`
   - Subscribe Topic: `deye/request`
   - Publish Topic: `deye/response`
4. Збережіть та перезавантажте EW11

**Налаштування Home Assistant:**
1. Виберіть протокол: **MQTT (via Mosquitto)**
2. Введіть:
   - Broker IP: `127.0.0.1` (якщо Mosquitto на тому ж ПК)
   - Broker Port: `1883`
   - **MQTT Username:** `mqtt_user`
   - **MQTT Password:** `mqtt_password_123`
   - Request Topic: `deye/request`
   - Response Topic: `deye/response`

> **💡 Примітка:** Username/Password опціональні - якщо залишити порожніми, підключення буде анонімним (потребує `allow_anonymous: true` в Mosquitto)

---

## 🤔 Який протокол обрати?

| Критерій | Modbus TCP | MQTT |
|----------|-----------|------|
| **Складність** | 🟢 Проста | 🟡 Середня |
| **Стабільність** | 🟡 Добра | 🟢 Відмінна |
| **Швидкість** | 🟢 Швидше | 🟡 Трохи повільніше |
| **Додаткове ПЗ** | ❌ Не потрібно | ✅ Mosquitto |
| **Для початківців** | ✅ | ❌ |

**Рекомендація:** Почніть з **Modbus TCP**. Якщо виникають проблеми зі стабільністю - переходьте на **MQTT**.

---

## 🔧 Сумісність

### Перевірені моделі інверторів:
- ✅ Deye SUN-5K-SG03LP1-EU
- ✅ Deye SUN-10K-SG04LP3-EU
- ✅ Deye SUN-12K-SG04LP3-EU
- ✅ (Більшість гібридних моделей Deye з підтримкою EW11)

### Вимоги:
- Home Assistant 2024.7.0 або новіше
- WiFi донгл EW11 підключений до інвертора
- Локальна мережа (інтеграція працює через Modbus TCP)

---

## 🐛 Відомі проблеми та їх вирішення

### Сенсори показують "Unavailable"
- Перевірте IP адресу та порт EW11
- Переконайтесь що EW11 підключений до WiFi
- Спробуйте збільшити інтервал оновлення до 10 сек
- Увімкніть кешування в налаштуваннях

### Неправильні значення потужності
- Переконайтесь що Slave ID правильний (зазвичай 1)
- Перезавантажте інвертор та EW11

### Генератор не відображається
- Переконайтесь що генератор фізично підключений
- Перевірте регістр 166 (0xA6) в налаштуваннях інвертора

---

## 📝 Ліцензія

MIT License - дивіться [LICENSE](https://github.com/byrsapty/zotac-deye-monitor/blob/main/LICENSE) для деталей.

---

## 🤝 Підтримка проєкту

Якщо ця інтеграція вам допомогла, поставте ⭐ на GitHub!

Знайшли баг або є ідея? [Створіть Issue](https://github.com/byrsapty/zotac-deye-monitor/issues)

---

## 👨‍💻 Автор

Розроблено з ❤️ для української спільноти Home Assistant.
