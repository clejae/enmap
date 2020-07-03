# Validation of validation image

import gdal
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import os

# level = "level3_lab"
sub = 'ba'

for level in ["level1_lab","level2_lab","level3_lab","level4_lab"]:
    comb_out_lst = []
    csv_path_comb = r'N:\temp\temp_akpona\x_calieco\07_accuracy_assessment\landsat_single_month\06\landsat_20130615_bap_{0}_all_subs_valimg_mean_{1}.csv'.format(
        sub, level)

    col_names = "Subset_Area, Class, R^2, Slope, Intercept, MAE, RMSE, INPUT\n"
    with open(csv_path_comb, "w") as f:
        f.write(col_names)

    for s in range(1, 7):
        for abr in ['landsat_20130615_bap']:
            print('Subset {0}'.format(s))

            # Input
            pred_path = r'N:\temp\temp_akpona\x_calieco\06_predictions\landsat_single_month\06\{3}_{0}_subset{1}_valimg_mean_{2}\aggregations\mean.bsq'.format(sub, s,
                                                                                                                    level,abr)
            ref_path = r'N:\temp\temp_akpona\x_calieco\05_ref_img\{0}\{0}_subset{1}_refimg_{2}.bsq'.format(sub, s, level)

            # Output
            out_path = r'N:\temp\temp_akpona\x_calieco\07_accuracy_assessment\landsat_single_month\06\{3}_{0}_subset{1}_valimg_mean_{2}'.format(sub, s, level, abr)
            csv_path = r'N:\temp\temp_akpona\x_calieco\07_accuracy_assessment\landsat_single_month\06\{3}_{0}_subset{1}_valimg_mean_{2}.csv'.format(
                sub, s, level, abr)

            #### PROCESSING
            try:
                os.mkdir(os.path.dirname(csv_path))
            except FileExistsError:
                print("Directory " + os.path.dirname(csv_path) + " already exists")

            try:
                os.mkdir(out_path)
            except FileExistsError:
                print("Directory " + out_path + " already exists")

            # create csv-file
            col_names = "Subset_Area, Class, R^2, Slope, Intercept, MAE, RMSE, Validation_type\n"
            with open(csv_path, "w") as f:
                f.write(col_names)

            if level == "level1_lab":
                class_dict = {
                    0 : "veg",
                    1 : "bac"
                }
            elif level == "level2_lab":
                class_dict = {
                    0: "wve",
                    1: "nvw",
                    2: "bac"
                }
            elif level == "level3_lab":
                class_dict = {
                    0: "tree",
                    1: "shrub",
                    2: "grass",
                    3: "background"
                }
            elif level == "level4_lab":
                class_dict = {
                    0: "con",
                    1: "bro",
                    2: "shr",
                    3: "gra",
                    4: "bac"
                }
            else:
                print("No dictionary defined in the script. You need to define a dictionary where the band numbers are assigned to a class!")

            name_list_pixel = []
            with open(ref_path[:-3] + "txt", "r") as f:
                for line in f:
                    line = line.replace("\n","")
                    name_list_pixel.append(line)
            f.close

            name_list_plot = name_list_pixel[0::9]
            name_list_plot = [name[-4:-2] for name in name_list_plot]

            pred_ras = gdal.Open(pred_path)
            ref_ras = gdal.Open(ref_path)

            pred_arr = pred_ras.ReadAsArray()
            ref_arr = ref_ras.ReadAsArray()

            num_bands = pred_ras.RasterCount

            for i in range(num_bands):

                # Bring data in right shape
                pred_band = pred_arr[i, :, :]
                ref_band = ref_arr[i, :, :]

                rows = pred_band.shape[0]
                cols = pred_band.shape[1]

                # Pixel-wise validation
                # X, regressor
                ref_band_pix = np.reshape(ref_band, (rows * cols))

                # Y, predictor
                pred_band_pix = np.reshape(pred_band, (rows * cols))

                # Drop NAN Values
                ref_band_pix = ref_band_pix[~np.isnan(pred_band_pix)]
                pred_band_pix = pred_band_pix[~np.isnan(pred_band_pix)]
                pred_band_pix = pred_band_pix[~np.isnan(ref_band_pix)]
                ref_band_pix = ref_band_pix[~np.isnan(ref_band_pix)]

                # reshape for model fitting
                ref_band_pix = ref_band_pix.reshape((-1, 1))

                        # Model Prediction
                model = LinearRegression()
                model.fit(ref_band_pix, pred_band_pix)

                r_sq = round(model.score(ref_band_pix, pred_band_pix), 3)
                intercept = round(model.intercept_, 3)
                slope = round(model.coef_[0], 3)
                errors = ref_band_pix - pred_band_pix.reshape((-1, 1))
                mae = round(np.mean(np.absolute(errors)), 3)
                rmse = round(np.sqrt(np.mean(errors*errors)), 3)

                # Write model parameters to csv
                with open(csv_path, "a") as f:
                    f.write( "subset" + str(s) + "," + class_dict[i] + "," + str(r_sq) + "," + str(slope) + "," + str(intercept) + "," + str(mae) + "," + str(rmse) + ", pixel-wise\n")

                ## plot figure
                font = {'family': 'Calibri',
                        'size': 24}

                plt.rc('font', **font)

                fig, ax = plt.subplots(figsize=(7,7))
                plt.gca().set_aspect('equal', adjustable='box')
                ax.scatter(ref_band_pix, pred_band_pix,  c = 'black', s = 40)
                ax.plot([0,1],[0,1], '--', c = 'black', linewidth = .5)
                ax.plot(pred_band_pix, slope * pred_band_pix + intercept, c = 'black', linewidth = 1)

                ax.spines["top"].set_bounds(.0, 1)
                ax.spines["bottom"].set_bounds(.0, 1)
                ax.spines["left"].set_position(("axes", .09))
                ax.spines["right"].set_position(("axes", 0.91))
                ax.axvspan(-0.05,0, color = "white")
                ax.axvspan(1, 1.05, color="white")
                plt.ylim(0, 1)
                # plt.text(.75, .05, "R^2 = " + str(r_sq), )
                props = dict(boxstyle='round', facecolor='white', alpha=0.5)
                plt.text(.40, .05, "y = "  + str(intercept)  + " + "+ str(slope) + "x",bbox=props)
                plt.text(.05, .90, "MAE = " + str(mae),bbox=props)
                # plt.text(.05, .77, "RMSE = " + str(rmse))
                # plt.title(class_dict[i])
                # plt.show()
                #plt.savefig(out_path + str(s) + "/" +  class_dict[i] + '_pixel-wise.png')
                plt.savefig(out_path + "/" + class_dict[i] + '_pixel-wise.png')
                plt.close()

                # Plot-wise
                # X, regressor
                ref_band_plot = np.mean(ref_band, 1)

                # Y, predictor
                pred_band_m = np.ma.masked_where(np.isnan(pred_band),pred_band)
                pred_band_plot = np.ma.mean(pred_band_m, 1)
                #pred_band_plot = np.reshape(pred_band, (rows * cols))

                # Drop NAN Values
                ref_band_plot = ref_band_plot[~np.isnan(pred_band_plot)]
                pred_band_plot = pred_band_plot[~np.isnan(pred_band_plot)]
                pred_band_plot = pred_band_plot[~np.isnan(ref_band_plot)]
                ref_band_plot = ref_band_plot[~np.isnan(ref_band_plot)]

                # reshape for model fitting
                ref_band_plot = ref_band_plot.reshape((-1, 1))

                # Model Prediction
                model_plot = LinearRegression()
                model_plot.fit(ref_band_plot, pred_band_plot)

                r_sq = round(model_plot.score(ref_band_plot, pred_band_plot), 3)
                intercept = round(model_plot.intercept_, 3)
                slope = round(model_plot.coef_[0], 3)
                errors = ref_band_plot - pred_band_plot.reshape((-1, 1))
                mae = round(np.mean(np.absolute(errors)), 3)
                rmse = round(np.sqrt(np.mean(errors * errors)), 3)

                # Write model parameters to csv
                with open(csv_path, "a") as f:
                    f.write("subset" + str(s) + "," + class_dict[i] + "," + str(r_sq) + "," + str(slope) + "," + str(
                        intercept) + "," + str(mae) + "," + str(rmse) + ", plot-wise\n")

                with open(csv_path_comb, "a") as f:
                    f.write("subset" + str(s) + "," + class_dict[i] + "," + str(r_sq) + "," + str(slope) + "," + str(
                        intercept) + "," + str(mae) + "," + str(rmse) + "," +  abr + "\n")

                # plot figure
                fig, ax = plt.subplots(figsize=(7, 7))
                plt.gca().set_aspect('equal', adjustable='box')
                ax.scatter(ref_band_plot, pred_band_plot, c='black', s=40)
                ax.plot([0, 1], [0, 1], '--', c='black', linewidth=.5)
                ax.plot(pred_band_plot, slope * pred_band_plot + intercept, c='black', linewidth=1)
                # for n, txt in enumerate(name_list_plot):
                #     ax.annotate(txt, (ref_band_plot[n],pred_band_plot[n]))
                ax.spines["top"].set_bounds(.0, 1)
                ax.spines["bottom"].set_bounds(.0, 1)
                ax.spines["left"].set_position(("axes", .087))
                ax.spines["right"].set_position(("axes", 0.912))
                ax.axvspan(-0.05, 0, color="white")
                ax.axvspan(1, 1.05, color="white")
                plt.ylim(0, 1)
                # plt.text(.75, .05, "R^2 = " + str(r_sq), )
                props = dict(boxstyle='round', facecolor='white', alpha=0.5)
                plt.text(.40, .05, "y = " + str(intercept) + " + " + str(slope) + "x", bbox=props)
                plt.text(.05, .90, "MAE = " + str(mae), bbox=props)
                # plt.text(.05, .80, "RMSE = " + str(rmse))
                # plt.title(class_dict[i])
                plt.xlabel("Reference")
                plt.ylabel("Prediction")
                plt.tight_layout()
                # plt.show()
                plt.savefig(out_path + "/" + class_dict[i] + '_plot-wise.png')

                plt.close()

        f.close

print('done')