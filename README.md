# Device Management Application for Raspberry Pi 4

Αυτή η εφαρμογή επιτρέπει την παρακολούθηση και τον έλεγχο συσκευών (όπως φώτα ή αντλίες) συνδεδεμένων με φυσικούς διακόπτες και ρελέ μέσω Raspberry Pi 4. Παρέχει web interface και υποστήριξη για MQTT.

---

## 🔧 Λειτουργίες

- CRUD για πολλές συσκευές (devices)
- Real-time ενημέρωση κατάστασης μέσω MQTT
- Υποστήριξη μεταφράσεων (π.χ. Ελληνικά)
- Διεπαφή Web με JavaScript (χωρίς frameworks)
- Αυτόματη εκκίνηση με `systemd` στο boot
- Υποστήριξη GPIO pins για είσοδο και έξοδο
- Unit και functional tests με pytest

---

## 📦 Εγκατάσταση 

### 1. Αποσυμπίεση του πακέτου

```bash
unzip device_app_package.zip
cd my_device_app
```

### 2α. Αν δεν επιτρέπεται η εγκατάσταση πακέτων στο externally-managed-environment

#### ✅ Προτεινόμενη Μέθοδος: Χρήση Virtual Environment
```bash
sudo apt update
sudo apt install python3-pip python3-venv -y
cd /home/pi/my_device_app
python3 -m venv venv
source venv/bin/activate
pip install flask flask-babel flask-cors flask-socketio eventlet paho-mqtt gpiod 
```

Για χρήση με systemd, αντικατέστησε το ExecStart στο device_app.service με:
```ini
ExecStart=/home/pi/my_device_app/venv/bin/python /home/pi/my_device_app/app.py
```

#### 🛠 Εναλλακτική Μέθοδος (με ρίσκο): Παράκαμψη του externally-managed-environment
Αν δεν χρησιμοποιείς virtual environment, μπορείς να κάνεις:

```bash
pip install --break-system-packages flask flask-babel paho-mqtt 
```
⚠️ Προσοχή: Αυτή η μέθοδος μπορεί να προκαλέσει προβλήματα στο σύστημα Python του Raspberry Pi.

### 2β. Αν επιτρέπεται η εγκατάσταση πακέτων στο externally-managed-environment

#### Εξαρτήσεις

```bash
sudo apt update
sudo apt install python3-pip
pip3 install flask flask-babel flask_cors flask-socketio eventlet paho-mqtt gpiod
```

### 3. systemd Υπηρεσία

Αντιγραφή της μονάδας systemd:

```bash
sudo cp device_app.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable device_app.service
sudo systemctl start device_app.service
```

Δες την κατάσταση:

```bash
sudo systemctl status device_app.service
```

Η εφαρμογή τρέχει στη θύρα 5000:
http://<IP_RPI>:5000/

---

## 🌐 Χρήση Web GUI

- Προσθήκη/Διαγραφή/Ενημέρωση συσκευών
- Ρυθμίσεις MQTT μέσω ξεχωριστής σελίδας
- Αυτόματη δημοσίευση/συνδρομή MQTT μηνυμάτων

---

## 🧪 Τεστ

### Απαιτούμενα

```bash
pip install pytest pytest-flask
```

### Τρέξιμο τεστ

```bash
pytest tests/
```

- Unit tests για τις βασικές οντότητες
- Functional tests για API routes

---

## 🌍 Μεταφράσεις

Βρίσκονται στον φάκελο:
```
translations/el/LC_MESSAGES/messages.po
```

Για μετάφραση άλλων γλωσσών, δημιουργήστε νέα γλώσσα με το `pybabel`.

---

## 📝 Δομή Pins

Για κάθε συσκευή απαιτούνται:
- `status` (είσοδος): pin που δείχνει αν ο διακόπτης είναι ανοικτός/κλειστός
- `enabled` (έξοδος): pin που ενεργοποιεί/απενεργοποιεί το relay
- `override` (έξοδος): pin που δίνει χειροκίνητα ρεύμα στο device

---

## 📂 Αρχεία

- `app.py`: Flask εφαρμογή
- `gpio_service.py`: GPIO διαχείριση
- `mqtt_service.py`: MQTT client
- `devices.json`: Αρχείο καταχώρησης συσκευών
- `config.json`: MQTT ρυθμίσεις
- `templates/`: HTML templates
- `static/app.js`: Web GUI JavaScript
- `translations/`: Μεταφράσεις
- `device_app.service`: systemd μονάδα
- `device.service`: Διαχείριση συσκευών
- `babel.cfg`: Παραμετροποίηση Babel για μεταφράσεις

---

## 🤝 Συνεισφορά

Ελεύθερα τροποποιήστε ή επεκτείνετε την εφαρμογή. Ιδανική για έργα αυτοματισμού ή εξοικονόμησης ενέργειας.

---

## 📧 Επικοινωνία

Για απορίες ή προτάσεις, δημιουργήστε ένα issue ή στείλτε μήνυμα.---

## ▶️ Χειροκίνητη Εκτέλεση της Εφαρμογής

Για να τρέξεις την εφαρμογή χωρίς systemd (χρήσιμο για δοκιμές ή debugging):

```bash
cd /home/pi/my_device_app
python3 app.py
```

Η εφαρμογή θα ξεκινήσει στο:
```
http://localhost:5000/
```

---

## 🌐 Επεξεργασία και Δημιουργία Μεταφράσεων

Χρησιμοποιούμε το `Flask-Babel` για την υποστήριξη μεταφράσεων.

### 1. Εγκατάσταση Babel

```bash
pip install Babel
```

### 2. Δημιουργία νέας μετάφρασης

Αν π.χ. θέλεις να προσθέσεις Γαλλικά (`fr`):

```bash
#pybabel extract -F babel.cfg -o messages.pot . <- θα διαβάσει και το folder του python virtual environment (venv)
pybabel extract -F babel.cfg -o messages.pot . --ignore-dirs=venv
pybabel init -i messages.pot -d translations -l fr
```

### 3. Επεξεργασία μεταφράσεων

Άνοιξε το αρχείο:
```
translations/fr/LC_MESSAGES/messages.po
```
και μετάφρασε κάθε `msgid`.

### 4. Μεταγλώττιση μεταφράσεων

Όταν τελειώσεις με τις μεταφράσεις:

```bash
pybabel compile -d translations
```

### 5. Ενημέρωση υπάρχουσας μετάφρασης

Αν αλλάξουν τα `msgid`:

```bash
pybabel extract -F babel.cfg -o messages.pot . --ignore-dirs=venv
pybabel update -i messages.pot -d translations
pybabel compile -d translations
```

---

## 📁 babel.cfg παράδειγμα

Δημιούργησε αρχείο `babel.cfg` στον root φάκελο με περιεχόμενο:

```
[python: **.py]
[jinja2: templates/**.html]
```

Αυτό επιτρέπει στο `pybabel` να αναλύει σωστά τόσο Python όσο και HTML αρχεία.

---