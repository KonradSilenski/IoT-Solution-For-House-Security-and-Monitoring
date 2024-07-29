import network
import socket
from time import sleep, localtime, strftime
import machine
from machine import Pin
from microdot import Microdot, Response, redirect

ssid = 'VM1582171'
password = 'bPccksZhwcfvsfg3'

app = Microdot()
Response.default_content_type = 'text/html'

button = Pin(21, Pin.IN, Pin.PULL_UP)

clients = set()

users = {
    'admin': 'iotapptest'
}

def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        print('Waiting for connection...')
        sleep(1)
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return ip

def get_current_time():
    t = localtime()
    return strftime('%Y-%m-%d %H:%M:%S', t)

def log_button_press():
    timestamp = get_current_time()
    with open('button_press_log.txt', 'a') as f:
        f.write(f'{timestamp}\n')

def read_log():
    try:
        with open('button_press_log.txt', 'r') as f:
            return f.read().splitlines()
    except OSError:
        return []

@app.route('/')
def home(request):
    if 'username' in request.cookies:
        username = request.cookies['username']
        log_entries = read_log()
        log_html = ''.join([f'<li>{entry}</li>' for entry in log_entries])
        return f"""
        <h3>Door Opening Log:</h3>
        <ul>{log_html}</ul>
        <a href="/logout">Logout</a>
        <button onclick="clearLogAndRefresh();">Clear Log and Refresh Page</button>
    <script>
        function clearLogAndRefresh() {{
            fetch('/clear-log', {{
                method: 'POST'
            }}).then(response => {{
                if (response.ok) {{
                    window.location.reload();
                }}
            }}).catch(error => {{
                console.error('Error:', error);
            }});
        }}
        
        function checkForUpdates() {{
            fetch('/check-updates')
            .then(response => {{
                if (response.ok) {{
                    return response.text();
                }} else {{
                    throw new Error('No network response');
                }}
            }})
            .then (data => {{
                if (data === 'reload') {{
                    window.location.reload();
                }}
            }})
            .catch(error => {{
                console.error('Error: ', error);
            }});
        }}
        
        checkForUpdates();
        
        setInterval(checkForUpdates, 150);
    </script>
        """
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login(request):
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and users[username] == password:
            response = redirect('/')
            response.set_cookie('username', username)
            return response
        return '<h2>Invalid input. Try again.</h2>'
    return """
    <h2>Login</h2>
    <form method="post">
      <label for="username">Username:</label>
      <input type="text" id="username" name="username" required><br><br>
      <label for="password">Password:</label>
      <input type="password" id="password" name="password" required><br><br>
      <input type="submit" value="Login">
    </form>
    """

@app.route('/logout')
def logout(request):
    response = redirect('/login')
    response.delete_cookie('username')
    return response

@app.route('/clear-log', methods=['POST'])
def clear_log(request):
    with open('button_press_log.txt', 'w') as f:
        pass  
    return '', 204


def button_pressed():
    return not button.value()

@app.route('/check-updates')
def check_updates(request):
    return 'reload' if button_pressed() else ''

def main_loop():
    while True:
        if button_pressed():
            log_button_press()
            sleep(1)
        sleep(0.1)

try:
    ip = connect()
    import _thread
    _thread.start_new_thread(main_loop, ())
    app.run(host=ip, port=80)
except KeyboardInterrupt:
    machine.reset()
