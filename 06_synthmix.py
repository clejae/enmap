# Unmixing of a single image or validation image

from hubflow.core import *
from sklearn.svm import SVR
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
import time

starttime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
print("Start time " + str(starttime))

# level = "level1_lab"
sub = 'lt'
for level in [ "level3_lab"]:
    print('\n', level)
    # for s in range(1,7):
    for abr in ['enmap_su']:
        # Input

        # lib_pth = r'N:\temp\temp_akpona\x_calieco\03_subsets_lib\enmap_su\{0}_speclib_{1}_subset{2}_mean.sli'.format(abr, sub, s)
        # in_ras_pth = r'N:\temp\temp_akpona\x_calieco\04_vali_img\enmap_su\{0}_{1}_subset{2}_valimg.bsq'.format(abr, sub, s)

        lib_pth = r'N:\temp\temp_akpona\x_calieco\03_subsets_lib\enmap_su\{0}_speclib_{1}_mean.sli'.format(abr, sub)
        in_ras_pth = r"N:\Project_California\99_temp\bcor\lt_temp\lt_mosaic\lt_mosaic_temp_nogaps.bsq"

        # Output
        # outdir = r'N:\temp\temp_akpona\x_calieco\06_predictions\enmap_su\{3}_{0}_subset{1}_valimg_mean_{2}/'.format(sub, s,
        #                                                                                                         level,abr)

        outdir = r'N:\temp\temp_akpona\x_calieco\06_predictions\enmap_su\{0}_{1}_fullimg_mean_{2}/'.format(abr,sub, level)

        ### PROCESSING
        library = EnviSpectralLibrary(filename=lib_pth)
        raster = Raster(filename=in_ras_pth)

        classification = Classification.fromEnviSpectralLibrary(filename='/vsimem/labels.bsq', library=library, attribute= level)
        classificationSample = ClassificationSample(raster=library.raster(), classification=classification)

        # build ensemble

        predictions = {target: list() for target in classificationSample.classification().classDefinition().labels()}
        runs = 10

        for run in range(runs):
            for target in classificationSample.classification().classDefinition().labels():
                stamp = '_run{}_target{}'.format(run + 1, target)
                # print('Subset ' + str(s),' ' + str(abr), stamp)
                print(stamp)

                fractionSample = classificationSample.synthMix(
                    filenameFeatures=join(outdir, 'train', 'features{}.bsq'.format(stamp)),
                    filenameFractions=join(outdir, 'train', 'fractions_{}.bsq'.format(stamp)),
                    mixingComplexities={2: 0.4, 3: 0.4, 4: 0.2}, classLikelihoods='proportional', #proportional
                    n=1000, target=target, includeWithinclassMixtures=True, includeEndmember=True)

                svr = SVR()
                param_grid = {'epsilon': [0.1], 'kernel': ['rbf'],
                              'gamma': [0.001],  # , 0.01, 0.1, 1, 10, 100, 1000],
                              'C': [1000]}  # , 0.01, 0.1, 1, 10, 100, 1000]}
                tunedSVR = GridSearchCV(cv=3, estimator=svr, scoring='neg_mean_absolute_error', param_grid=param_grid)
                scaledAndTunedSVR = make_pipeline(StandardScaler(), tunedSVR)
                regressor = Regressor(sklEstimator=scaledAndTunedSVR)
                regressor.fit(sample=fractionSample)
                prediction = regressor.predict(filename=join(outdir, 'predictions', 'prediction{}.bsq'.format(stamp)), raster=raster)

                predictions[target].append(prediction)

        # aggregate

        applier = Applier()
        for target in predictions:
            for i, regression in enumerate(predictions[target]):
                applier.setFlowRegression(name='{}_{}'.format(str(target), i), regression=regression)

        for key in ['mean']:
        #for key in ['mean', 'std', 'median', 'iqr']:
            applier.setOutputRaster(name=key, filename=join(outdir, 'aggregations', '{}.bsq'.format(key)))

        class Aggregate(ApplierOperator):
            def ufunc(self, predictions):
                #results = {key: list() for key in ['mean', 'std', 'median', 'iqr']}
                results = {key: list() for key in ['mean']}

                # reduce over runs and stack targets
                for target in predictions:
                    array = list()
                    for i, regression in enumerate(predictions[target]):
                        print(regression.filename())
                        array_i = self.flowRegressionArray(name='{}_{}'.format(str(target), i), regression=regression)
                        array.append(array_i)

                    array = np.array(array)
                    np.clip(array, a_min=0, a_max=1, out=array) # clip to 0-1
                    results['mean'].append(np.mean(array, axis=0))
                    # results['std'].append(np.std(array, axis=0))
                    # p25, median, p75 = np.percentile(array, q=[25, 50, 75], axis=0)
                    # results['median'].append(median)
                    # results['iqr'].append(p75-p25)

                # normalize to 0-1
                #for key in ['mean', 'median']:
                for key in ['mean']:
                    total = np.sum(results[key], axis=0)
                    results[key] = [a / total for a in results[key]]

                for key in ['mean']:
                # for key in ['mean', 'std', 'median', 'iqr']:
                    self.outputRaster.raster(key=key).setArray(results[key])

        applier.apply(operatorType=Aggregate, predictions=predictions)

        # RGB
        # for key in ['mean']:
        # # for key in ['mean', 'median']:
        #     fraction = Fraction(filename=join(outdir, 'aggregations', '{}.bsq'.format(key)),
        #                         classDefinition=classificationSample.classification().classDefinition())
        #     #fraction.asClassColorRGBRaster(filename=join(outdir, 'rgb', '{}_rgb.bsq'.format(key)))

endtime = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())

print("Start time " + str(starttime))
print("End time " + str(endtime))