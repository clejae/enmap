import pandas as pd
import numpy as np
sub = 'ba'
abr = '\landsat_spectemp_metr'
s = 1
for s in range(1,7):
    csv_pth_mean = r'N:\temp\temp_akpona\x_calieco\03_subsets_lib\\landsat_spectemp_metr\{0}_speclib_{1}_subset{2}_mean.csv'.format(abr, sub, s)
    csv_pth_pix = r'N:\temp\temp_akpona\x_calieco\03_subsets_lib\\landsat_spectemp_metr\{0}_speclib_{1}_subset{2}_pix.csv'.format(abr, sub, s)

    df_mean = pd.read_csv(csv_pth_mean)
    df_mean['level2_lab'] = np.where(df_mean['level3_lab'] == 'gra', 'nvw', np.where(df_mean['level3_lab'] == 'bac', 'bac', 'wve'))
    df_mean['level1_lab'] = np.where(df_mean['level3_lab'] == 'bac', 'bac', 'veg')

    df_pix = pd.read_csv(csv_pth_pix)
    df_pix['level2_lab'] = np.where(df_pix['level3_lab'] == 'gra', 'nvw',
                                     np.where(df_pix['level3_lab'] == 'bac', 'bac', 'wve'))
    df_pix['level1_lab'] = np.where(df_pix['level3_lab'] == 'bac', 'bac', 'veg')

    df_mean.to_csv(csv_pth_mean, ',', index=False)
    df_pix.to_csv(csv_pth_pix, ',', index=False)