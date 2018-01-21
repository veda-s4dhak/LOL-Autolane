# ================================ LOCAL IMPORTS ================================ #

import screen_capture as sc
import datetime

# ================================ MAIN ================================ #

if __name__ == '__main__':

    rgb = sc.initialize_rgb_array()

    directory = r'C:\\Users\\Veda Sadhak\\Desktop\\LOL-Autolane\\raw_dataset'
    file_name = r'\\raw_'

    initial_time = datetime.datetime.now()

    for i in range (0,10):

        rgb = sc.get_screen_capture(rgb, directory=directory, filename=file_name+str(i), save=False, show_image=True)
        elapsed_time = datetime.datetime.now()-initial_time
        #print(rgb)
        print(elapsed_time)
        #time.sleep(0.5)