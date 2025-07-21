import time
import pyautogui

print("Click into Notepad or your game window...")
time.sleep(5)

pyautogui.press("space")
print("Pressed SPACE")

time.sleep(1)
pyautogui.press("a")
print("Pressed A")

time.sleep(1)
pyautogui.press("enter")
print("Pressed ENTER")
