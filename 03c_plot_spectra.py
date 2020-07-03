import gdal
import shutil
import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

sub = 'ba'
for s in range(1,7):
    for abr in ['spectemp_metr_QT2','spectemp_metr_QT3']:

        input_name = r'N:\temp\temp_akpona\x_calieco\03_subsets_lib\landsat_spectemp_metr\landsat_{0}_{1}_subset{2}_pix.sli'.format(abr, sub, s)
        mem_name = r'N:\temp\temp_akpona\x_calieco\03_subsets_lib\landsat_spectemp_metr\landsat_{0}_{1}_subset{2}_pix_mem.sli'.format(abr, sub, s)

        output_path = r'N:\temp\temp_akpona\x_calieco\03_subsets_lib\plots\landsat_{0}_{1}_subset{2}\\'.format(abr, sub, s)
        output_description = r'landsat_{0}_{1}_subset{2}'.format(abr, sub, s)

        ### PROCESSING
        # create output folder
        try:
            os.mkdir(output_path)
        except FileExistsError:
            print("Directory " + output_path + " already exists")

        # create temporary copy of spectral library with its header file
        # copy is renamed to bsq-file because python can't handle spectral library file
        # the header file is also accordingly edited
        shutil.copyfile(input_name, mem_name)
        shutil.copyfile(input_name[:-3] + 'hdr', mem_name[:-3] + 'hdr')

        file = open(mem_name[:-3] + "hdr").read()
        file = file.replace('file type = ENVI Spectral Library', 'file type = ENVI Standard')
        with open(mem_name[:-3] + "hdr", 'w') as out_file:
            out_file.write(file)
        out_file.close

        # open temporary spectral library

        ras = gdal.Open(mem_name) #ras = gdal.Open(input_name[:-4] + "_mem.bsq")
        arr = ras.ReadAsArray()

        max_refl = np.max(arr)
        min_refl = np.min(arr)

        # read spectra names from header file and save to a list
        try:
            start = file.index("spectra names = ") + len("spectra names = {") # index of last character if this string
            end = file.index("}", start) # index of first appearance of given character after start index
            plot_names= file[start:end] # string between these two indices
            plot_names = plot_names.split(",") # string to list
        except ValueError:
            print("Could not read spectra names from header file.")

        # extract plot number by first splitting pixel number and plot number and
        # second splitting plot number and subset abbreveation
        plot_names_clean = [name.split("-")[0] for name in plot_names]
        plot_names_clean = [name.split("_")[0] for name in plot_names]

        # identify unique plot numbers
        plot_names_set = set(plot_names_clean)
        plot_names_set = sorted(plot_names_set)

        meta = pd.read_csv(input_name[:-3] + "csv")

        # loop over unique plot numbers
        # extract all indices where plot number occurs in plot number list
        # plot array at indices

        for entry in plot_names_set:
            print(entry)
            index_list = [i for i, e in enumerate(plot_names_clean) if e == entry]
            num_spec = len(index_list)

            if num_spec > 1 :

                arr_sub = arr[index_list, :]
                std_arr = np.std(arr_sub, 0)
                std_arr_mean = np.round(np.mean(std_arr),2)

            else:
                std_arr_mean = 0

            # extract level3 name
            x = index_list[0]
            class_name = meta.iloc[x]['level3_lab']

            fig, ax = plt.subplots(figsize=(10, 10))
            for index in index_list:
                ax.plot(range(arr.shape[1]),arr[index,:])

            plt.ylim(min_refl, max_refl)
            plt.title(entry + ' - ' + class_name)
            plt.text(0, (max_refl - 200), "number of spectra = " + str(num_spec))
            plt.text(0, (max_refl - 350), "mean std dev of bands = " + str(std_arr_mean))
            plt.savefig(output_path + output_description + class_name + '_plot' + entry + '.png')
            plt.close()

        del(ras)
        del(file)

        # remove temporary files
        os.remove(mem_name)
        os.remove(mem_name[:-3] + "hdr")

print("done")

