⚡ Switchify – Smart Home Automation

A Smart Home Automation System built using Raspberry Pi, featuring voice control, Markov chain-based behavior learning, and scenario scheduling through a web interface.

---

🚀 Features

🎤 Voice Control

- Control devices using voice commands
- Supports English + Hindi/Marathi mix
- Examples:
  - "Light 1 on"
  - "Fan band karo"
  - "Good night" → Turns everything OFF
  - "Light bright / dim / normal"

---

💡 3-in-1 Smart Light (Light2)

- Bright Mode
- Dim Mode
- Normal Mode
- Can be triggered directly using voice

---

🔄 Multi-Device Voice Commands

- Control multiple devices in one command:
  - "Turn on light and fan"
  - "Fan and light off"

---

⏱️ Timer via Voice

- Set timers using voice:
  - "Light on for 10 minutes"
  - "Fan for 30 seconds"

---

🧠 Markov Chain Automation

- Learns user behavior patterns
- Automatically repeats actions at learned time
- Works only when time matches (demo-friendly)

---

📅 Scenario Scheduling

- Set custom schedules via UI
- Example:
  - Turn on lights at 6:30 PM for 20 minutes

---

🌐 Web Dashboard

- Control all devices from browser
- Features:
  - Live clock
  - Device toggle buttons
  - Auto mode switch
  - Scenario manager
  - Power usage monitor

---

⚡ Energy Usage Tracking

- Tracks power consumption of:
  - Light1
  - Light2
  - Fan
- Displays total energy usage in real-time

---

🛠️ Tech Stack

- Python (Flask) – Backend server
- SpeechRecognition – Voice input
- Raspberry Pi GPIO – Device control
- HTML + JS – Web interface
- Threading – Parallel task execution

---

📁 Project Structure

Switchify/
│── main6.py        # Main Flask server + logic
│── control.py      # GPIO/device control
│── templates/      # (Optional HTML templates)
│── README.md

---

▶️ How to Run

1. Clone the repo

git clone https://github.com/your-username/Switchify-Smart-Home-Automation.git
cd Switchify

2. Install dependencies

pip install flask SpeechRecognition pyaudio

3. Run the project

python3 main6.py

4. Open in browser

http://<raspberry-pi-ip>:5000

---

🧪 Example Voice Commands

Command| Action
Light 1 on| Turns ON Light1
Fan off| Turns OFF Fan
Good night| Turns OFF all devices
Light bright| Sets Light2 to bright
Fan for 5 minutes| Runs fan for 5 min

---

⚠️ Notes

- Requires microphone connected to Raspberry Pi
- Internet required for Google Speech Recognition
- GPIO pins must be configured correctly in "control.py"

---

🔮 Future Improvements

- Mobile app integration
- Offline voice recognition
- AI-based predictive automation
- MQTT / IoT cloud integration

---

👨‍💻 Author

Aryan Hinge

---

📜 License

MIT License

---

⭐ If you like this project

Give it a ⭐ on GitHub!
