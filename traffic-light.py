import customtkinter as ctk
from PIL import Image, ImageTk
import time
import threading
from datetime import datetime, time as dt_time
import tkinter.messagebox  # Importing the standard messagebox
import requests  # For making HTTP requests to get the time
import winsound  # For playing sound on Windows

class ControlWindow:
    def __init__(self, traffic_light):
        self.window = ctk.CTkToplevel()
        self.window.title("Điều khiển đèn giao thông")
        self.window.geometry("370x400")  # Increased size for new buttons
        
        self.traffic_light = traffic_light
        
        # Frame chứa các nút điều khiển
        control_frame = ctk.CTkFrame(self.window)
        control_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Các nút điều khiển
        ctk.CTkButton(control_frame, text="Vàng nháy", 
                     width=200,
                     command=self.traffic_light.toggle_yellow_blink).pack(pady=5)
        ctk.CTkButton(control_frame, text="Ưu tiên",
                     width=200,
                     command=self.traffic_light.toggle_priority).pack(pady=5)
        ctk.CTkButton(control_frame, text="Cài đặt",
                     width=200,
                     command=self.traffic_light.show_settings).pack(pady=5)
        
        # Nút hiển thị thông tin
        ctk.CTkButton(control_frame, text="Thông tin", 
                     width=200,
                     command=self.show_info).pack(pady=5)

        # Nút bật/tắt đèn rẽ phải
        self.right_turn_button = ctk.CTkButton(control_frame, text="Bật/Tắt Đèn Rẽ Phải", 
                     width=200,
                     command=self.toggle_right_turn_light)
        self.right_turn_button.pack(pady=5)
        self.right_turn_light_state = False  # Initialize the state of the right turn light

        # Nút cập nhật thời gian
        self.update_time_button = ctk.CTkButton(control_frame, text="Cập Nhật Thời Gian", 
                     width=200,
                     command=self.update_time)
        self.update_time_button.pack(pady=5)
        self.time_label = ctk.CTkLabel(control_frame, text="", font=("Arial", 10))  # Label for displaying time
        self.time_label.pack(pady=5)

        # Nút thoát chương trình
        ctk.CTkButton(control_frame, text="Thoát", 
                     width=200,
                     command=self.exit_program, 
                     fg_color="red").pack(pady=5)

        # Nút quay lại
        ctk.CTkButton(control_frame, text="Quay lại", 
                     width=200,
                     command=self.close_window).pack(pady=5)

    def show_info(self):
        info_message = "Tên chương trình: Đèn Giao Thông\nPhiên bản: 1.0\nTác giả: Namtran5905\nMô tả: Chương trình điều khiển đèn giao thông."
        tkinter.messagebox.showinfo("Thông tin chương trình", info_message)  # Using standard messagebox

    def toggle_right_turn_light(self):
        # Logic to toggle the right turn light
        self.right_turn_light_state = not self.right_turn_light_state  # Toggle the state
        
        if self.right_turn_light_state:
            self.blinking_thread = threading.Thread(target=self.blink_right_turn_light)
            self.blinking_thread.start()  # Start the blinking thread
        else:
            self.traffic_light.running = False  # Stop the blinking

    def blink_right_turn_light(self):
        self.traffic_light.running = True  # Allow blinking
        while self.traffic_light.running and self.right_turn_light_state:
            self.traffic_light.right_turn_light.configure(fg_color="orange")
            time.sleep(0.5)
            self.traffic_light.right_turn_light.configure(fg_color="darkgray")
            time.sleep(0.5)

    def update_time(self):
        self.update_time_button.configure(state="disabled")  # Disable the button
        self.time_label.configure(text="Loading...")  # Show loading text

        def fetch_time():
            try:
                # Fetching time from a time server
                response = requests.get('http://worldtimeapi.org/api/timezone/Etc/UTC')
                if response.status_code == 200:
                    time_data = response.json()
                    current_time = time_data['datetime']
                    # Update the program's time accordingly
                    self.time_label.configure(text=f"Thời gian đã được cập nhật: {current_time}")  # Update the label with the new time
                    tkinter.messagebox.showinfo("Cập Nhật Thời Gian", "Thời gian đã được cập nhật thành công.")
                else:
                    tkinter.messagebox.showerror("Lỗi", "Không thể cập nhật thời gian.")
            except requests.exceptions.RequestException as e:
                tkinter.messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {str(e)}")
            finally:
                self.update_time_button.configure(state="normal")  # Re-enable the button

        threading.Thread(target=fetch_time).start()  # Start the time fetching in a separate thread

    def exit_program(self):
        self.window.destroy()  # Close the control window
        self.settings_window.destroy()  # Close the settings window if it's open
        self.root.destroy()  # Close the main application window

    def close_window(self):
        self.window.destroy()  # Close the control window

class TrafficLight:
    def __init__(self):
        # Cửa sổ chính
        self.root = ctk.CTk()
        self.root.title("Đèn Giao Thông")
        self.root.geometry("350x590")  # Giảm kích thước
        
        # Biến điều khiển
        self.running = True
        self.yellow_blink = False
        self.priority = False
        self.right_turn_light_state = False  # Initialize the state of the right turn light
        
        # Thời gian mặc định
        self.times = {
            'red': 30,
            'green': 25,
            'yellow': 3,
            'peak_red': 20,
            'peak_green': 15,
            'peak_yellow': 3
        }
        self.peak_times = [(dt_time(7, 0), dt_time(9, 0))]  # List of tuples for multiple peak times
        
        # Initialize peak start and end times
        self.peak_start = dt_time(7, 0)  # Default start time for peak hours
        self.peak_end = dt_time(9, 0)    # Default end time for peak hours
        
        # Tạo giao diện chính
        self.setup_main_window()
        
        # Tạo cửa sổ cài đặt
        self.setup_settings_window()
        
        # Bắt đầu luồng điều khiển đèn
        self.control_thread = threading.Thread(target=self.control_lights, daemon=True)
        self.control_thread.start()
        
        # Bắt đầu luồng điều khiển đèn rẽ phải
        self.right_turn_thread = threading.Thread(target=self.control_right_turn_light, daemon=True)
        self.right_turn_thread.start()

    def setup_main_window(self):
        # Frame chứa đèn
        lights_frame = ctk.CTkFrame(self.root, width=150, height=400)  # Giảm kích thước
        lights_frame.pack(pady=15)  # Giảm padding
        
        # Đồng hồ đếm ngược
        self.timer_label = ctk.CTkLabel(lights_frame, width=80, height=80,  # Giảm kích thước
                                      text="00", font=("Arial", 32, "bold"),  # Giảm font
                                      fg_color="black", text_color="yellow",
                                      corner_radius=40)
        self.timer_label.pack(pady=8)  # Giảm padding
        
        # Đèn đỏ
        self.red_light = ctk.CTkLabel(lights_frame, width=80, height=80,  # Giảm kích thước
                                    text="", fg_color="darkred", corner_radius=40)
        self.red_light.pack(pady=8)  # Giảm padding
        
        # Đèn vàng
        self.yellow_light = ctk.CTkLabel(lights_frame, width=80, height=80,  # Giảm kích thước
                                       text="", fg_color="darkgray", corner_radius=40)
        self.yellow_light.pack(pady=8)  # Giảm padding
        
        # Đèn xanh
        self.green_light = ctk.CTkLabel(lights_frame, width=80, height=80,  # Giảm kích thước
                                      text="", fg_color="darkgreen", corner_radius=40)
        self.green_light.pack(pady=8)  # Giảm padding
        
        # Đèn người đi bộ
        self.pedestrian_light = ctk.CTkLabel(lights_frame, width=40, height=40,  # Giảm kích thước
                                           text="👤", fg_color="darkgray", corner_radius=20)
        self.pedestrian_light.pack(pady=4)  # Giảm padding
        
        # Frame cho đèn rẽ phải và chú thích
        right_turn_frame = ctk.CTkFrame(lights_frame)
        right_turn_frame.pack(pady=4)  # Giảm padding
        
        # Đèn rẽ phải màu cam với mũi tên
        self.right_turn_light = ctk.CTkLabel(right_turn_frame, width=40, height=40,  # Giảm kích thước
                                           text="➜", font=("Arial", 16),  # Giảm font
                                           fg_color="darkgray", text_color="white",
                                           corner_radius=20)
        self.right_turn_light.pack(side="left", padx=4)  # Giảm padding
        
        # Chú thích cho đèn rẽ phải
        ctk.CTkLabel(right_turn_frame, text="Xe 2 bánh\nđược phép rẽ phải",
                    font=("Arial", 10)).pack(side="left", padx=4)  # Giảm font và padding
        
        # Nút mở cửa sổ điều khiển
        ctk.CTkButton(self.root, text="Mở Cửa Sổ Điều Khiển", command=self.open_control_window).pack(pady=10)

    def open_control_window(self):
        self.control_window = ControlWindow(self)

    def setup_settings_window(self):
        self.settings_window = ctk.CTkToplevel(self.root)
        self.settings_window.title("Cài đặt")
        self.settings_window.geometry("400x590")
        self.settings_window.withdraw()
        
        # Frame thời gian đèn bình thường
        normal_frame = ctk.CTkFrame(self.settings_window)
        normal_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(normal_frame, text="Thời gian đèn bình thường (giây)").pack()
        
        # Đèn đỏ
        red_frame = ctk.CTkFrame(normal_frame)
        red_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(red_frame, text="Đèn đỏ:").pack(side="left", padx=5)
        self.red_entry = ctk.CTkEntry(red_frame, width=50)
        self.red_entry.pack(side="left", padx=5)
        self.red_entry.insert(0, str(self.times['red']))
        
        # Đèn xanh
        green_frame = ctk.CTkFrame(normal_frame)
        green_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(green_frame, text="Đèn xanh:").pack(side="left", padx=5)
        self.green_entry = ctk.CTkEntry(green_frame, width=50)
        self.green_entry.pack(side="left", padx=5)
        self.green_entry.insert(0, str(self.times['green']))
        
        # Đèn vàng
        yellow_frame = ctk.CTkFrame(normal_frame)
        yellow_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(yellow_frame, text="Đèn vàng:").pack(side="left", padx=5)
        self.yellow_entry = ctk.CTkEntry(yellow_frame, width=50)
        self.yellow_entry.pack(side="left", padx=5)
        self.yellow_entry.insert(0, str(self.times['yellow']))
        
        # Frame thời gian đèn giờ cao điểm
        peak_frame = ctk.CTkFrame(self.settings_window)
        peak_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(peak_frame, text="Thời gian đèn giờ cao điểm (giây)").pack()
        
        # Đèn đỏ cao điểm
        peak_red_frame = ctk.CTkFrame(peak_frame)
        peak_red_frame.pack(side="left", padx=5, pady=5)
        ctk.CTkLabel(peak_red_frame, text="Đèn đỏ:").pack(side="left", padx=5)
        self.peak_red_entry = ctk.CTkEntry(peak_red_frame, width=50)
        self.peak_red_entry.pack(side="left", padx=5)
        self.peak_red_entry.insert(0, str(self.times['peak_red']))
        
        # Đèn xanh cao điểm
        peak_green_frame = ctk.CTkFrame(peak_frame)
        peak_green_frame.pack(side="left", padx=5, pady=5)
        ctk.CTkLabel(peak_green_frame, text="Đèn xanh:").pack(side="left", padx=5)
        self.peak_green_entry = ctk.CTkEntry(peak_green_frame, width=50)
        self.peak_green_entry.pack(side="left", padx=5)
        self.peak_green_entry.insert(0, str(self.times['peak_green']))
        
        # Đèn vàng cao điểm
        peak_yellow_frame = ctk.CTkFrame(peak_frame)
        peak_yellow_frame.pack(side="left", padx=5, pady=5)
        ctk.CTkLabel(peak_yellow_frame, text="Đèn vàng:").pack(side="left", padx=5)
        self.peak_yellow_entry = ctk.CTkEntry(peak_yellow_frame, width=50)
        self.peak_yellow_entry.pack(side="left", padx=5)
        self.peak_yellow_entry.insert(0, str(self.times['peak_yellow']))
        
        # Thời gian cao điểm
        peak_time_frame = ctk.CTkFrame(self.settings_window)
        peak_time_frame.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(peak_time_frame, text="Thời gian cao điểm (HH:MM)").pack()
        
        # Giờ bắt đầu
        start_frame = ctk.CTkFrame(peak_time_frame)
        start_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(start_frame, text="Bắt đầu:").pack(side="left", padx=5)
        self.peak_start_entry = ctk.CTkEntry(start_frame, width=100)
        self.peak_start_entry.pack(side="left", padx=5)
        self.peak_start_entry.insert(0, self.peak_start.strftime("%H:%M"))
        
        # Giờ kết thúc
        end_frame = ctk.CTkFrame(peak_time_frame)
        end_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(end_frame, text="Kết thúc:").pack(side="left", padx=5)
        self.peak_end_entry = ctk.CTkEntry(end_frame, width=100)
        self.peak_end_entry.pack(side="left", padx=5)
        self.peak_end_entry.insert(0, self.peak_end.strftime("%H:%M"))
        
        # Nút lưu
        ctk.CTkButton(self.settings_window, text="Lưu", 
                     command=self.save_settings).pack(pady=10)

        # Nút quay lại
        ctk.CTkButton(self.settings_window, text="Quay lại", 
                     command=self.close_settings_window).pack(pady=10)

    def save_settings(self):
        try:
            # Lưu thời gian đèn bình thường
            self.times['red'] = int(self.red_entry.get()) if self.red_entry.get() else self.times['red']
            self.times['green'] = int(self.green_entry.get()) if self.green_entry.get() else self.times['green']
            self.times['yellow'] = int(self.yellow_entry.get()) if self.yellow_entry.get() else self.times['yellow']
            
            # Lưu thời gian đèn cao điểm
            self.times['peak_red'] = int(self.peak_red_entry.get()) if self.peak_red_entry.get() else self.times['peak_red']
            self.times['peak_green'] = int(self.peak_green_entry.get()) if self.peak_green_entry.get() else self.times['peak_green']
            self.times['peak_yellow'] = int(self.peak_yellow_entry.get()) if self.peak_yellow_entry.get() else self.times['peak_yellow']
            
            # Lưu thời gian cao điểm
            start_time = datetime.strptime(self.peak_start_entry.get(), "%H:%M").time() if self.peak_start_entry.get() else self.peak_start
            end_time = datetime.strptime(self.peak_end_entry.get(), "%H:%M").time() if self.peak_end_entry.get() else self.peak_end
            self.peak_start = start_time
            self.peak_end = end_time
            
            self.settings_window.withdraw()
        except ValueError as e:
            # Hiển thị thông báo lỗi
            error_label = ctk.CTkLabel(self.settings_window, 
                                     text="Lỗi: Vui lòng nhập đúng định dạng",
                                     text_color="red")
            error_label.pack()
            self.root.after(2000, error_label.destroy)

    def close_settings_window(self):
        self.settings_window.withdraw()  # Close the settings window

    def show_settings(self):
        self.settings_window.deiconify()

    def toggle_yellow_blink(self):
        """Bật/tắt chế độ vàng nháy"""
        self.yellow_blink = not self.yellow_blink
        self.priority = False

    def toggle_priority(self):
        """Bật/tắt chế độ ưu tiên"""
        self.priority = not self.priority
        self.yellow_blink = False

    def is_peak_hour(self):
        """Kiểm tra có phải giờ cao điểm không"""
        current_time = datetime.now().time()
        if self.peak_start <= self.peak_end:
            return self.peak_start <= current_time <= self.peak_end
        else:  # Trường hợp khoảng thời gian qua nửa đêm
            return current_time >= self.peak_start or current_time <= self.peak_end

    def control_right_turn_light(self):
        """Điều khiển đèn rẽ phải nhấp nháy"""
        while self.running:
            self.right_turn_light.configure(fg_color="orange")
            time.sleep(0.5)
            self.right_turn_light.configure(fg_color="darkgray")
            time.sleep(0.5)

    def control_lights(self):
        while self.running:
            if self.yellow_blink:
                # Chế độ vàng nháy
                self.red_light.configure(fg_color="darkgray")
                self.green_light.configure(fg_color="darkgray")
                self.pedestrian_light.configure(fg_color="darkgray")
                self.timer_label.configure(text="--")
                
                self.yellow_light.configure(fg_color="yellow")
                time.sleep(0.5)
                self.yellow_light.configure(fg_color="darkgray")
                time.sleep(0.5)
                
            elif self.priority:
                # Chế độ ưu tiên
                self.red_light.configure(fg_color="darkgray")
                self.yellow_light.configure(fg_color="darkgray")
                self.green_light.configure(fg_color="lime")
                self.pedestrian_light.configure(fg_color="darkgray")
                self.timer_label.configure(text="--")
                time.sleep(0.1)
                
            else:
                # Chế độ bình thường
                times = self.times if not self.is_peak_hour() else {
                    'red': self.times['peak_red'],
                    'green': self.times['peak_green'],
                    'yellow': self.times['peak_yellow']
                }
                
                # Đèn đỏ
                self.red_light.configure(fg_color="red")
                self.yellow_light.configure(fg_color="darkgray")
                self.green_light.configure(fg_color="darkgray")
                self.pedestrian_light.configure(fg_color="lime")
                
                for i in range(times['red'], 0, -1):
                    if self.yellow_blink or self.priority:
                        break
                    self.timer_label.configure(text=str(i))
                    time.sleep(1)
                
                if not (self.yellow_blink or self.priority):
                    # Đèn xanh
                    self.red_light.configure(fg_color="darkgray")
                    self.yellow_light.configure(fg_color="darkgray")
                    self.green_light.configure(fg_color="lime")
                    self.pedestrian_light.configure(fg_color="darkgray")
                    
                    for i in range(times['green'], 0, -1):
                        if self.yellow_blink or self.priority:
                            break
                        self.timer_label.configure(text=str(i))
                        time.sleep(1)
                    
                    # Đèn vàng
                    if not (self.yellow_blink or self.priority):
                        self.red_light.configure(fg_color="darkgray")
                        self.yellow_light.configure(fg_color="yellow")
                        self.green_light.configure(fg_color="darkgray")
                        self.pedestrian_light.configure(fg_color="darkgray")
                        
                        for i in range(times['yellow'], 0, -1):
                            if self.yellow_blink or self.priority:
                                break
                            self.timer_label.configure(text=str(i))
                            time.sleep(1)

    def run(self):
        try:
            self.root.mainloop()
        finally:
            self.running = False
            if self.control_thread.is_alive():
                self.control_thread.join()
            if self.right_turn_thread.is_alive():
                self.right_turn_thread.join()

if __name__ == "__main__":
    app = TrafficLight()
    app.run()
