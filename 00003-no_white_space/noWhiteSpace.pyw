import tkinter as tk
import pyperclip


def name_to_folder_name():
    text="BitYad.xyz - "
    text+=ent_name.get()

    lbl_result_1_info["text"] = text
    copy_to_clipboard(text)
    lbl_result_1_msg["text"] = "copied"
    lbl_result_1_msg["fg"] = "green"



def name_to_Rar_file_name():
    text="BitYad.xyz - "
    text+=ent_name.get()

    for i in range(len(text)):
        if text[i-1]==" ":
            temp_x=text[i].capitalize()
            text=text[:i]+temp_x+text[i+1:]

    text= text.replace(" ","")
    text+=".rar"

    lbl_result_2_info["text"] = text
    copy_to_clipboard(text)
    lbl_result_2_msg["text"] = "copied"
    lbl_result_2_msg["fg"] = "green"


def name_to_Rar_file_name_for_url():
    text="BitYad.xyz - "
    text+=ent_name.get()

    for i in range(len(text)):
        if text[i-1]==" ":
            temp_x=text[i].capitalize()
            text=text[:i]+temp_x+text[i+1:]

    text= text.replace(" ","")
    return text

def url_maker():
    temp_url="http://"
    temp_url+=ent_url.get()
    temp_url+="/"
    temp_url+=name_to_Rar_file_name_for_url()
    temp_url+=".part"

    return temp_url

def full_url_maker():
    temp_copy=""
    for i in range(int(ent_url_count.get())):
        temp_url=url_maker()

        if int(ent_url_count.get()) >= 10 and i < 9:
            temp_url+="0"

        temp_url+=str(i+1)
        temp_url+=".rar"

        temp_copy+=temp_url
        temp_copy+="\n"

        text_box = tk.Label(master=window, text=temp_url)
        text_box.grid(row=5+i, column=0)

        text_box_msg = tk.Label(master=window, text="copied", fg="green")
        text_box_msg.grid(row=5+i, column=1)
    
    copy_to_clipboard(temp_copy)


def copy_to_clipboard(x):
    pyperclip.copy(x)



window = tk.Tk()
window.title("BitYad.xyz Renamer")
window.columnconfigure(0, minsize=250)
window.rowconfigure(0, minsize=100)
window.columnconfigure([1, 2, 3], minsize=250)
window.rowconfigure([1, 2, 3, 4], minsize=50)

frame_a = tk.Frame(master=window)

label = tk.Label(
    master=frame_a,
    text="""
    تبدیل اسم به نام بیت یاد
    ساخته شده توسط آقا جـــــــواد
    """,
    font=("FarhangFaNum MediumSharp", 20)
)

label.grid(row=0, column=0)
frame_a.grid(row=0, column=0, columnspan = 4)


frm_entry_1 = tk.Frame(master=window)
frm_entry_2 = tk.Frame(master=window)

frm_entry_2.columnconfigure([0, 1], minsize=250)
frm_entry_2.rowconfigure([0, 1], minsize=30)

ent_name = tk.Entry(master=frm_entry_1, width=55)
lbl_name = tk.Label(master=frm_entry_1, text="Enter the Name: ")

ent_url = tk.Entry(master=frm_entry_2, width=15)
lbl_url = tk.Label(master=frm_entry_2, text="Enter the server ip/Domain: ")
ent_url.insert(tk.END, '51.210.71.101')

ent_url_count = tk.Entry(master=frm_entry_2, width=4)
lbl_url_count = tk.Label(master=frm_entry_2, text="Enter Number of Parts: ")

ent_name.grid(row=1, column=1)
lbl_name.grid(row=1, column=0)

ent_url.grid(row=0, column=1)
lbl_url.grid(row=0, column=0)
ent_url_count.grid(row=1, column=1)
lbl_url_count.grid(row=1, column=0)



btn_convert_1 = tk.Button(
    master=window,
    text="Run Folder Name",
    command=name_to_folder_name
)
btn_convert_2 = tk.Button(
    master=window,
    text="Run Rar File Name",
    command=name_to_Rar_file_name
)

btn_url = tk.Button(
    master=window,
    text="Run Url Maker",
    command=full_url_maker
)

lbl_result_1 = tk.Label(master=window, text="Folder Name: ")
lbl_result_1_info = tk.Label(master=window, text="...")
lbl_result_1_msg = tk.Label(master=window, text="...")

lbl_result_2 = tk.Label(master=window, text="Rar File Name: ")
lbl_result_2_info = tk.Label(master=window, text="...")
lbl_result_2_msg = tk.Label(master=window, text="...")

lbl_result_2 = tk.Label(master=window, text="Rar File Name: ")
lbl_result_2_info = tk.Label(master=window, text="...")
lbl_result_2_msg = tk.Label(master=window, text="...")

frm_entry_1.grid(row=1, column=0)
frm_entry_2.grid(row=4, column=0)

btn_convert_1.grid(row=1, column=1)
btn_convert_2.grid(row=1, column=2)
btn_url.grid(row=1, column=3)

lbl_result_1.grid(row=2, column=0)
lbl_result_1_info.grid(row=2, column=1)
lbl_result_1_msg.grid(row=2, column=2)

lbl_result_2.grid(row=3, column=0)
lbl_result_2_info.grid(row=3, column=1)
lbl_result_2_msg.grid(row=3, column=2)


window.mainloop()
