import socket
import threading
import json
import time
import pytest

HOST = '127.0.0.1'
PORT = 2001

@pytest.fixture(scope="module")
def mock_tcp_simulator():
    """Фикстура для создания фонового мок-сервера TCP-симулятора"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    
    stop_server = threading.Event()
    
    def server_loop():
        while not stop_server.is_set():
            try:
                server.settimeout(0.5)
                client_sock, addr = server.accept()
                
                test_signals = []
                for i in range(1, 11):
                    test_signals.append({
                        "id": i,
                        "name": f"Signal_{i}",
                        "value": round(10.5 * i, 2),
                        "quality": "Good",
                        "time": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                
                packet = (json.dumps(test_signals) + "\n").encode('utf-8')
                client_sock.sendall(packet)
                client_sock.close()
            except socket.timeout:
                continue
            except Exception:
                break
        server.close()

    thread = threading.Thread(target=server_loop)
    thread.start()
    
    yield
    
    stop_server.set()
    thread.join()

def test_client_connection_and_data_parsing(mock_tcp_simulator):
    """Тест проверяет подключение к TCP-серверу и валидацию структуры данных"""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(2.0)
    
    try:
        client.connect((HOST, PORT))
        
        buffer = b""
        while b"\n" not in buffer:
            data = client.recv(1024)
            if not data:
                break
            buffer += data
            
        signals_data = json.loads(buffer.decode('utf-8').strip())
        
        assert len(signals_data) == 10, f"Ожидалось 10 сигналов, но получено {len(signals_data)}"
        
        for signal in signals_data:
            assert "id" in signal, "В сигнале отсутствует поле 'id'"
            assert "name" in signal, "В сигнале отсутствует поле 'name'"
            assert "value" in signal, "В сигнале отсутствует поле 'value'"
            assert "quality" in signal, "В сигнале отсутствует поле 'quality'"
            assert "time" in signal, "В сигнале отсутствует поле 'time'"
            
            assert isinstance(signal["id"], int), f"ID должен быть integer, а не {type(signal['id'])}"
            assert signal["quality"] in ["Good", "Bad"], "Неверное значение качества сигнала"

    except socket.error as e:
        pytest.fail(f"Не удалось подключиться к TCP-серверу: {e}")
    finally:
        client.close()
