import glob
import os
import shutil

reference_file = r'N:\temp\temp_akpona\x_calieco\03_subsets_lib\enmap_su\enmap_su_speclib_ba_subset1_mean.json'

# 'BLU_QT2', 'GRN_QT2', 'RED_QT2', 'NIR_QT2', 'SW1_QT2', 'SW2_QT2'
for abr in ['spectemp_metr_QT2','spectemp_metr_QT3']:
    list_of_targets = glob.glob(r'N:\temp\temp_akpona\x_calieco\03_subsets_lib\landsat_spectemp_metr\*{0}*.csv'.format(abr))

    # 'N:\temp\temp_akpona\x_calieco\03_subsets_lib\landsat_tc_tsi\landsat_{0}_{1}_subset{2}.sli'.format(abr, sub, s)

    for i, file in enumerate(list_of_targets):
        print(i+1, file)
        target_file = file[:-3] + str('json')
        shutil.copyfile(reference_file, target_file)