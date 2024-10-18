import pandas as pd
from sklearn.linear_model import LogisticRegression
import numpy as np
import math
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import norm
import matplotlib.pyplot as plt
from sklearn.feature_selection import RFECV
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.decomposition import PCA
from sklearn.cross_decomposition import PLSRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

from sklearn import set_config
set_config(display='diagram')


# Summary for Logistic Regression model from scikit
def summaryLogReg(modelpipe, X: pd.core.frame.DataFrame, y: pd.core.series.Series):
    """Summary of scikit 'LogisticRegression' models.
    
    Provide feature information of linear regression models,
    such as coefficient, standard error and p-value. It is adapted
    to stand-alone and Pipeline scikit models.
    
    Important restriction of the function is that LogisticRegression 
    must be the last step of the Pipeline.
    Args:
        model: LogisticRegression or Pipeline model
        X (pd.core.frame.DataFrame): Input variables dataframe
        y (pd.core.series.Series): Output variable series
    """
    # Select model from pipeline
        # Obtain coefficients of the model
    if type(modelpipe) is not LogisticRegression:
        model = modelpipe[len(modelpipe) - 1]  
        prep = modelpipe[len(modelpipe) - 2] 
        # Obtain names of the inputs
        try:
            coefnames = [x.split("__")[1] for x in  list(prep.get_feature_names_out())]
        except:
            coefnames = list(prep.get_feature_names_out())
    else:
        model = modelpipe  
        prep = []
        # Obtain names of the inputs
        coefnames = [column for column in X.columns]
    
    # Obtain coefficients of the model
    coefs = model.coef_[0]
    intercept = model.intercept_
    if not intercept == 0:
        coefs = np.append(intercept,coefs)
        coefnames.insert(0,'Intercept')
    # Calculate matrix of predicted class probabilities.
    # Check resLogit.classes_ to make sure that sklearn ordered your classes as expected
    predProbs = modelpipe.predict_proba(X)
    y_pred = predProbs[:,1]
    y_int = y.cat.codes.to_numpy()
    res = y_int - y_pred
    print('Deviance Residuals:')
    quantiles = np.quantile(res, [0,0.25,0.5,0.75,1], axis=0)
    quantiles = pd.DataFrame(quantiles, index=['Min','1Q','Median','3Q','Max'])
    print(quantiles.transpose())
    # Print coefficients of the model
    print('\nCoefficients:')
    coefs = pd.DataFrame(data=coefs, index=coefnames, columns=['Estimate'])
    ## Calculate std error of inputs ------------- 
    #scale if necessary and build Xdesign
    if prep:
        X_trainMOD = prep.fit_transform(X)
    else:
        X_trainMOD = X
    
    if not intercept == 0:
        X_design = np.hstack([np.ones((X.shape[0], 1)), X_trainMOD])
    else:
        X_design = X_trainMOD
    # Initiate matrix of 0's, fill diagonal with each predicted observation's variance
    V = np.diagflat(np.prod(predProbs, axis=1))
    # Covariance matrix
    covLogit = np.linalg.inv(X_design.T @ V @ X_design)
    print(coefs)
    # Std errors
    coefs['Std. Err'] = np.sqrt(np.diag(covLogit))
    # t-value
    coefs['t-value'] = coefs['Estimate'] / coefs['Std. Err']
    # P-values
    coefs['Pr(>|t|)'] = (1 - norm.cdf(abs(coefs['t-value']))) * 2
    coefs['Signif'] = coefs['Pr(>|t|)'].apply(lambda x: '***' if x < 0.001 else ('**' if x < 0.01 else ('*' if x < 0.05 else ('.' if x < 0.1 else ' '))))
    print(coefs)
    print('---\nSignif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1')
    ## AIC criterion ----------------
    # Obtain rank of the model
    rank = len(coefs)
    likelihood = y_pred * y_int + (1 - y_pred) * (1 - y_int)
    AIC = 2*rank - 2*math.log(likelihood.max())
    #print('AIC:',AIC,' (no es fiable, revisar formula de AIC)')
    return

def plotModelGridError(model, figsize=(12, 6), xscale:str="linear", xscale2:str="linear", param1:str=None, param2:str=None):
    """Plot model cross-validation error along grid of hyperparameters

    Args:
        model: model to analyze
        figsize (tuple[float, float], optional): figure of plot size. Defaults to (12, 6).
        xscale (str, optional): Scale of x-axis of first plot. Defaults to "linear".
        xscale2 (str, optional): Scale of x-axis of second plot. Defaults to "linear".
        param1 (str, optional): First parameter of the grid to analyze. Defaults to None.
        param2 (str, optional): Second parameter of the grid to analyze. Defaults to None.

    Raises:
        TypeError: No hyperparameters found in grid, grid must have some hyperparameter to create plot
    """
    cv_r = model.cv_results_
    err = cv_r["mean_test_score"]
    std = cv_r["std_test_score"]
    param_names = list(model.cv_results_.keys())
    if param1 is not None and param2 is not None:
        param_names = ["param_"+param1, "param_"+param2]
    param_keys = [s for s in param_names if "param_" in s]
    params = [s.split("param_")[1] for s in param_keys]
        
    best_params = model.best_params_
    if not param_keys:
        raise TypeError("No hyperparameters encountered in grid.")
    if len(param_keys) > 1:
        grid1 = model.cv_results_[param_keys[0]].data
        cat1 = 'num'
        if not(type(grid1[0]) == int or type(grid1[0]) == float):
            grid1 = [p for p in list(grid1)]
            cat1 = 'cat'
        param_name1 = " ".join(params[0].split("__")[1].split("_"))
        grid2 = model.cv_results_[param_keys[1]].data
        cat2 = 'num'
        if not(type(grid2[0]) == int or type(grid2[0]) == float):
            grid2 = [p  for p in list(grid2)]
            cat2 = 'cat'
        param_name2 = " ".join(params[1].split("__")[1].split("_"))

        cols        = ['cv_error', 'cv_std']
        multi_index = pd.MultiIndex.from_tuples([(p1, p2) for p1, p2 in sorted(zip(grid1, grid2))], names=[param1, param2])
        dfe         = pd.DataFrame([(e, s) for e, s in zip(err, std)], columns=cols, index=multi_index)
        # First hyperparameter
        plt.figure(figsize=figsize)
        ax = plt.gca()
        dfe.unstack(level=1)['cv_error'].plot(ax=ax, style='o-', yerr=dfe.unstack(level=1)['cv_std'])
        #reset color cycle so that the marker colors match
        ax.set_prop_cycle(None)
        #plot the markers
        sc = dfe.unstack(level=1)['cv_error'].plot(figsize=(12,8), style='o-', markersize=5, ax=ax)
        handles, labels = ax.get_legend_handles_labels()
        handles = handles[0:int(len(labels)/2)]
        labels = labels[0:int(len(labels)/2)]
        ax.legend(handles,labels,loc="lower right", title=param_name2)
        if not cat1 == 'cat':
            plt.plot(model.best_params_[params[0]], model.best_score_, marker="o", markersize=15, color="red")
        else:
            pos = list(dfe.unstack(level=1).index).index(model.best_params_[params[0]])
            plt.plot(pos, model.best_score_, marker="o", markersize=15, color="red")
        plt.title(f"Best model with {params[0]} = {str(best_params[params[0]])} and {params[1]} = {str(best_params[params[1]])} ")
        plt.xlabel(param_name1)
        plt.xscale(xscale)
        plt.show()
        # Second hyperparameter
        plt.figure(figsize=figsize)
        dfe.unstack(level=0)['cv_error'].plot(ax=plt.gca(), style='o-', yerr=dfe.unstack(level=1)['cv_std'])
        #reset color cycle so that the marker colors match
        plt.gca().set_prop_cycle(None)
        #plot the markers
        dfe.unstack(level=0)['cv_error'].plot(figsize=(12,8), style='o-', markersize=5, ax = plt.gca())
        handles, labels = plt.gca().get_legend_handles_labels()
        handles = handles[0:int(len(labels)/2)]
        labels = labels[0:int(len(labels)/2)]
        plt.gca().legend(handles,labels,loc="lower right", title=param_name1)
        if not cat2 == 'cat':
            plt.plot(model.best_params_[params[1]], model.best_score_, marker="o", markersize=15, color="red")
        else:
            pos = list(dfe.unstack(level=0).index).index(model.best_params_[params[1]])
            plt.plot(pos, model.best_score_, marker="o", markersize=15, color="red")
        plt.title(f"Best model with {params[0]} = {str(best_params[params[0]])} and {params[1]} = {str(best_params[params[1]])} ")
        plt.xlabel(param_name2)
        plt.xscale(xscale2)
        plt.show()
    else:
        grid=model.cv_results_[param_keys[0]].data
        if not(type(grid[0]) == int or type(grid[0]) == float):
            grid = [p for p in list(grid)]
        param_name= " ".join(params[0].split("__")[1].split("_"))
        
        plt.figure(figsize=figsize)
        plt.errorbar(grid, err, yerr=std, linestyle="None", ecolor='lightblue')
        plt.plot(grid, err, marker="o", markersize=10, c='lightblue')
        plt.plot(model.best_params_[params[0]], model.best_score_, marker="o", markersize=15, color="red")
        plt.title(f"Best model with {params[0]} = {str(best_params[params[0]])} ")
        plt.xlabel(param_name)
        plt.xscale(xscale)
        plt.show()
    return

# Import necessary modules
from turtle import pos
import numpy as np
import math
import pandas as pd
from scipy.stats import norm, binomtest
from statsmodels.stats import contingency_tables as cont_tab
import seaborn as sns
import itertools 
from numpy.matlib import repmat
import matplotlib.pyplot as plt
import warnings
import sklearn.metrics as mtrs
import matplotlib.collections 
import numbers
import six
from sklearn.calibration import calibration_curve
import matplotlib.lines as mlines
from sklearn.linear_model import LogisticRegression
# from sklearn.inspection import DecisionBoundaryDisplay

# Summary for Logistic Regression model from scikit
def summaryLogReg(modelpipe, X: pd.core.frame.DataFrame, y: pd.core.series.Series):
    """Summary of scikit 'LogisticRegression' models.
    
    Provide feature information of linear regression models,
    such as coefficient, standard error and p-value. It is adapted
    to stand-alone and Pipeline scikit models.
    
    Important restriction of the function is that LogisticRegression 
    must be the last step of the Pipeline.
    Args:
        model: LogisticRegression or Pipeline model
        X (pd.core.frame.DataFrame): Input variables dataframe
        y (pd.core.series.Series): Output variable series
    """
    # Select model from pipeline
        # Obtain coefficients of the model
    if type(modelpipe) is not LogisticRegression:
        model = modelpipe[len(modelpipe) - 1]  
        prep = modelpipe[len(modelpipe) - 2] 
        # Obtain names of the inputs
        try:
            coefnames = [x.split("__")[1] for x in  list(prep.get_feature_names_out())]
        except:
            coefnames = list(prep.get_feature_names_out())
    else:
        model = modelpipe  
        prep = []
        # Obtain names of the inputs
        coefnames = [column for column in X.columns]
    
    # Obtain coefficients of the model
    coefs = model.coef_[0]
    intercept = model.intercept_
    if not intercept == 0:
        coefs = np.append(intercept,coefs)
        coefnames.insert(0,'Intercept')
    # Calculate matrix of predicted class probabilities.
    # Check resLogit.classes_ to make sure that sklearn ordered your classes as expected
    predProbs = modelpipe.predict_proba(X)
    y_pred = predProbs[:,1]
    y_int = y.cat.codes.to_numpy()
    res = y_int - y_pred
    print('Deviance Residuals:')
    quantiles = np.quantile(res, [0,0.25,0.5,0.75,1], axis=0)
    quantiles = pd.DataFrame(quantiles, index=['Min','1Q','Median','3Q','Max'])
    print(quantiles.transpose())
    # Print coefficients of the model
    print('\nCoefficients:')
    coefs = pd.DataFrame(data=coefs, index=coefnames, columns=['Estimate'])
    ## Calculate std error of inputs ------------- 
    #scale if necessary and build Xdesign
    if prep:
        X_trainMOD = prep.fit_transform(X)
    else:
        X_trainMOD = X
    
    if not intercept == 0:
        X_design = np.hstack([np.ones((X.shape[0], 1)), X_trainMOD])
    else:
        X_design = X_trainMOD
    # Initiate matrix of 0's, fill diagonal with each predicted observation's variance
    V = np.diagflat(np.prod(predProbs, axis=1))
    # Covariance matrix
    covLogit = np.linalg.inv(X_design.T @ V @ X_design)
    print(coefs)
    # Std errors
    coefs['Std. Err'] = np.sqrt(np.diag(covLogit))
    # t-value
    coefs['t-value'] = coefs['Estimate'] / coefs['Std. Err']
    # P-values
    coefs['Pr(>|t|)'] = (1 - norm.cdf(abs(coefs['t-value']))) * 2
    coefs['Signif'] = coefs['Pr(>|t|)'].apply(lambda x: '***' if x < 0.001 else ('**' if x < 0.01 else ('*' if x < 0.05 else ('.' if x < 0.1 else ' '))))
    print(coefs)
    print('---\nSignif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1')
    ## AIC criterion ----------------
    # Obtain rank of the model
    rank = len(coefs)
    likelihood = y_pred * y_int + (1 - y_pred) * (1 - y_int)
    AIC = 2*rank - 2*math.log(likelihood.max())
    #print('AIC:',AIC,' (no es fiable, revisar formula de AIC)')
    return
    
def expandgrid(*itrs):
    product = list(itertools.product(*itrs))
    return {'Var{}'.format(i+1):[x[i] for x in product] for i in range(len(itrs))}

def plot2DClass(X: pd.core.frame.DataFrame, y: pd.core.series.Series, model, var1:str, var2:str, selClass:str=None, np_grid=200, figsize=(10,10)):
    """Create plots focused on explaining classification model performance

    Plots created by this function tries to show how the model classifies
    samples in X in 2D plots.
    Args:
        X (pd.core.frame.DataFrame): dataframe containing input variables
        y (pd.core.series.Series): series containing output variable
        model: Classification model to be analyzed
        var1 (str): name of the variable of the x-axis in the plots
        var2 (str): name of the variable of the y-axis in the plots
        selClass (str, optional): Positive class of the output variable Defaults to None.
        np_grid (int, optional): number of points of the grid in first and second plot when 
        using only two input variables. Defaults to 200.
        figsize (tuple, optional): size of figure. Defaults to (10,10).

    Raises:
        ValueError: X must have at least 2 input variables
        ValueError: var1 and var2 must be column names of X
    """
    if X.shape[1] < 2:
        raise ValueError("X must have at least 2 input variables")
    if isinstance(X, pd.DataFrame):
        c_names = [column for column in X.columns]
        if any(not elem in c_names for elem in [var1, var2]):
            nelems = [not elem in c_names for elem in [var1, var2]]
            err_str = " and ".join(list(itertools.compress([var1,var2], nelems))) + ' could not be found in X.'
            raise ValueError(err_str)

    # Predict input data
    df = X.copy()
    try:
        df['pred'] = model.predict(X)
    except:
        df['pred'] = model.predict(X.values)
    output_name = y.name
    # Check positive class
    if selClass is None:
        selClass = y.unique()[0]
        warnings.warn('The first level of the output would be use as positive class', category=UserWarning)
    selClass = str(selClass)
    if len(df.columns) == 3:
        np_X1 = np.linspace(df[var1].min(), df[var1].max(), np_grid)
        np_X2 = np.linspace(df[var2].min(), df[var2].max(), np_grid)
        X, Y = np.meshgrid(np_X1, np_X2)
        # grid_X1_X2 = pd.DataFrame(CT.expandgrid(np_X1, np_X2))
        palette = {y.unique()[0]:'C0', y.unique()[1]:'C1'} # Needed to maintain color palette    
        grid_X1_X2 = pd.DataFrame(np.c_[X.ravel(), Y.ravel()], columns=[var1,var2])
        # Predict each point of the grid
        try:
            grid_X1_X2['pred'] = model.predict(grid_X1_X2)
        except:
            grid_X1_X2['pred'] = model.predict(grid_X1_X2.values)
        grid_X1_X2.columns = [var1, var2, output_name]
        # Obtain probabilites of the model in the grid and add to the grid data frame
        try:
            probabilities = model.predict_proba(grid_X1_X2[[var1,var2]])
        except:
            probabilities = model.predict_proba(grid_X1_X2[[var1,var2]].values)
        grid_X1_X2 = grid_X1_X2.join(pd.DataFrame(np.round(probabilities,2)))
        grid_X1_X2.columns = [var1, var2, output_name] + ['_'.join(['prob',lev]) if isinstance(lev, str) else '_'.join(['prob',str(np.round(lev, 2))]) for lev in y.unique()]
        # Define output class variable in grid
        grid_X1_X2['prob'] = grid_X1_X2['_'.join(['prob',selClass])]
        # Classification of input space
        
        _, axes = plt.subplots(2, 2, figsize=figsize)
        sns.scatterplot(x=var1, y=var2, hue=output_name, palette=palette, ax=axes[0, 0], data=grid_X1_X2).set_title('Classification of input space')
        handles,labels = axes[0, 0].get_legend_handles_labels()
        handles = [l for _, l in sorted(zip(labels, handles))]
        labels = sorted(labels)
        axes[0, 0].legend(handles,labels)
        # DecisionBoundaryDisplay.from_estimator(
        #     model,
        #     X,
        #     cmap=plt.cm.RdYlBu,
        #     response_method="predict",
        #     ax=ax,
        #     xlabel=var1,
        #     ylabel=var2,
        # )
        # Probabilities estimated for input space
        y_prob = grid_X1_X2['prob'].to_numpy().reshape(np_grid,np_grid)
        sns.scatterplot(x=var1, y=var2, hue='prob', data=grid_X1_X2, palette=sns.color_palette("Blues", as_cmap=True), ax=axes[0, 1]).set_title(' '.join(["Probabilities estimated for input space, class:",selClass]))
        
        
        # Classification results
        df2 = pd.concat([df.reset_index(),interaction(y, df['pred']).reset_index()], axis=1)
        del df2['index']
        sns.scatterplot(x=var1, y=var2, hue='inter', data= df2, ax=axes[1, 0]).set_title(' '.join(["Classification results, class:", selClass]))
        
        df[output_name] = y
        sns.scatterplot(x=var1, y=var2, hue=output_name, palette=palette, data=df, ax=axes[1, 1]).set_title(' '.join(['Classes and estimated probability contour lines for class:', selClass]))
        cnt = plt.contour(X, Y, y_prob, colors='black')
        plt.clabel(cnt, inline=True, fontsize=8)
        axes[1, 1].legend(handles,labels)
        plt.tight_layout(pad=4.0)
        plt.show()
    else:
        df[output_name] = y
        # Classification results
        df2 = pd.concat([df.reset_index(),interaction(y, df['pred']).reset_index()], axis=1)
        plt.subplot(121)
        sns.scatterplot(x=var1, y=var2, hue='inter', data=df2).set_title('Classification of input space')        
        plt.subplot(122)
        df[output_name] = y
        sns.scatterplot(x=var1, y=var2, hue=output_name, data=df).set_title(' '.join(['Classes and estimated probability contour lines for class:', selClass]))
        plt.tight_layout(pad=4.0)
        plt.show()
    return

def interaction(var1, var2, returntype='Series'):
    dVar1 = pd.get_dummies(var1)
    dVar2 = pd.get_dummies(var2)
    names1 = dVar1.columns[np.concatenate(repmat(np.arange(len(dVar1.columns)), len(dVar2.columns), 1).transpose())]
    names2 = dVar2.columns[np.concatenate(repmat(np.arange(len(dVar2.columns)), 1, len(dVar1.columns)).transpose())]
    namesdef = ["_".join([str(name1),str(name2)]) for name1, name2 in zip(names1, names2)]
    inter = pd.DataFrame(np.multiply(dVar1.iloc[:, np.concatenate(repmat(np.arange(len(dVar1.columns)), len(dVar2.columns), 1).transpose())].to_numpy(), dVar2.iloc[:, np.concatenate(repmat(np.arange(len(dVar2.columns)), 1, len(dVar1.columns)).transpose())].to_numpy()), columns = namesdef)
    if returntype == 'Series':
        return pd.Series(inter.idxmax(axis=1), name='inter')
    else:
        return inter

def confusion_matrix(y_true:pd.core.series.Series, y_pred:pd.core.series.Series, labels, sample_weight=None, normalize:bool=True):
    """Calculate confusion matrix and classification metrics
 
    Args:
        y_true (pd.core.series.Series): Series containing true values of output
        y_pred (pd.core.series.Series): Series containing predicted values of output
        labels [str,str,str,...]: String vector of output categories
        sample_weight ([int, int, ...], optional): Weights assigned to output samples in training process. Defaults to None.
        normalize (bool, optional): normalize classification metrics when possible. Defaults to True.
    """
 
    # Calculate confusion matrix
    print('Confusion Matrix and Statistics\n\t   Prediction')
    # if labels is None:
    #     labels = list(y_true.unique())
    cm = mtrs.confusion_matrix(y_true, y_pred, labels=labels, sample_weight=sample_weight, normalize=None)
    cm_df = pd.DataFrame(cm, columns=labels)
    cm_df = pd.DataFrame(labels, columns=['Reference']).join(cm_df)
    print(cm_df.to_string(index=False))
    # Calculate metrics depending on type of classification, multiclass or binary
    try:  
        if len(y_true.unique()) == 2: # binary
            average = 'binary'
        else: # multiclass
            average = 'macro'    
    except:
        if len(np.unique(y_true)) == 2: # binary
            average = 'binary'
        else: # multiclass
            average = 'macro'
           
    # Calculate accuracy
    acc = mtrs.accuracy_score(y_true, y_pred, normalize=normalize, sample_weight=sample_weight)
    # Calculate No Information Rate
    combos = np.array(np.meshgrid(y_pred, y_true)).reshape(2, -1)
    noi = mtrs.accuracy_score(combos[0], combos[1], normalize=normalize, sample_weight=sample_weight)
    # Calculate p-value Acc > NIR
    res = binomtest(cm.diagonal().sum(), cm.sum(), max(pd.DataFrame(cm).apply(sum,axis=1)/cm.sum()),'greater')
    # Calculate P-value mcnemar test
    MCN_pvalue = cont_tab.mcnemar(cm).pvalue
    # Calculate Kappa
    Kappa = mtrs.cohen_kappa_score(y_true, y_pred, labels=labels, sample_weight=sample_weight)
    # Obtain positive label
    pos_label = labels[0]
    # Calculate precision
    precision = mtrs.precision_score(y_true, y_pred, labels=labels, pos_label=pos_label, average=average, sample_weight=sample_weight)
    # Calculate recall
    recall = mtrs.recall_score(y_true, y_pred, labels=labels, pos_label=pos_label, average=average, sample_weight=sample_weight)
    # Calculate F1 score
    F_score = mtrs.f1_score(y_true, y_pred, labels=labels, pos_label=pos_label, average=average, sample_weight=sample_weight)
    # Calculate balanced accuracy
    Balanced_acc = mtrs.balanced_accuracy_score(y_true, y_pred, sample_weight=sample_weight)
    if average == 'binary': # binary
        # Calculate sensitivity, specificity et al
        TP = cm[1,1]
        TN = cm[0,0]
        FP = cm[0,1]
        FN = cm[1,0]
        sens = TP / (TP + FN)
        spec = TN / (TN + FP)
        Prevalence = (TP + FN) / (TP + TN + FP + FN)
        Detection_rate = TP / (TP + TN + FP + FN)
        Detection_prevalence = (TP + FP) /  (TP + TN + FP + FN)
       
       
        # print all the measures
        out_str = '\nAccuracy: ' + str(round(acc,2)) + '\n' + \
        'No Information Rate: ' + str(round(noi,2)) + '\n' + \
        'P-Value [Acc > NIR]: ' + str(round(res.pvalue, 2)) + '\n' + \
        'Kappa: ' + str(round(Kappa,2)) + '\n' + \
        'Mcnemar\'s Test P-Value: ' + str(round(MCN_pvalue,2)) + '\n' + \
        'Sensitivity: ' + str(round(sens,2)) + '\n' + \
        'Specificity: ' + str(round(spec,2)) + '\n' + \
        'Precision: ' + str(round(precision,2)) + '\n' + \
        'Recall: ' + str(round(recall,2)) + '\n' + \
        'Prevalence: ' + str(round(Prevalence,2)) + '\n' + \
        'Detection Rate: ' + str(round(Detection_rate,2)) + '\n' + \
        'Detection prevalence: ' + str(round(Detection_prevalence,2)) + '\n' + \
        'Balanced accuracy: ' + str(round(Balanced_acc,2)) + '\n' + \
        'F1 Score: ' + str(round(F_score,2)) + '\n' + \
        'Positive label: ' + str(pos_label)
    else: # multiclass
                # print all the measures
        out_str = '\nAccuracy: ' + str(round(acc,2)) + '\n' + \
        'No Information Rate: ' + str(round(noi,2)) + '\n' + \
        'P-Value [Acc > NIR]: ' + str(round(res,2)) + '\n' + \
        'Kappa: ' + str(round(Kappa,2)) + '\n' + \
        'Mcnemar\'s Test P-Value: ' + str(round(MCN_pvalue,2)) + '\n' + \
        'Precision: ' + str(round(precision,2)) + '\n' + \
        'Recall: ' + str(round(recall,2)) + '\n' + \
        'Balanced accuracy: ' + str(round(Balanced_acc,2)) + '\n' + \
        'F1 Score: ' + str(round(F_score,2))  + '\n' + \
        'Positive label: ' + str(pos_label)
    print(out_str)
    
        

def make_segments(x, y):
    '''
    Create list of line segments from x and y coordinates,
    in the correct format for LineCollection:
    an array of the form
    numlines x (points per line) x 2 (x and y) array
    '''

    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    return segments


def colorline(x, y, z=None, axes=None,
            cmap=plt.get_cmap('coolwarm'),
            norm=plt.Normalize(0.0, 1.0), linewidth=3, alpha=1.0,
            **kwargs):
    '''
    Plot a colored line with coordinates x and y
    Optionally specify colors in the array z
    Optionally specify a colormap, a norm function and a line width
    '''

    # Default colors equally spaced on [0,1]:
    if z is None:
        z = np.linspace(0.0, 1.0, len(x))

    # Special case if a single number:
    if isinstance(z, numbers.Real):
        z = np.array([z])

    z = np.asarray(z)

    segments = make_segments(x, y)
    lc = matplotlib.collections.LineCollection(
        segments, array=z, cmap=cmap, norm=norm,
        linewidth=linewidth, alpha=alpha, **kwargs
    )

    if axes is None:
        axes = plt.gca()

    axes.add_collection(lc)
    axes.autoscale()

    return lc


def plot_roc(tpr, fpr, thresholds, subplots_kwargs=None,
            label_every=None, label_kwargs=None,
            fpr_label='False Positive Rate',
            tpr_label='True Positive Rate',
            luck_label='Luck',
            title='Receiver operating characteristic',
            **kwargs):

    if subplots_kwargs is None:
        subplots_kwargs = {}

    figure, axes = plt.subplots(1, 1, **subplots_kwargs)

    if 'lw' not in kwargs:
        kwargs['lw'] = 1

    axes.plot(fpr, tpr, **kwargs)

    if label_every is not None:
        if label_kwargs is None:
            label_kwargs = {}

        if 'bbox' not in label_kwargs:
            label_kwargs['bbox'] = dict(
                boxstyle='round,pad=0.5', fc='yellow', alpha=0.5,
            )

        for k in six.moves.range(len(tpr)):
            if k % label_every != 0:
                continue

            threshold = str(np.round(thresholds[k], 2))
            x = fpr[k]
            y = tpr[k]
            axes.annotate(threshold, (x, y), **label_kwargs)

    if luck_label is not None:
        axes.plot((0, 1), (0, 1), '--', color='Gray')

    lc = colorline(fpr, tpr, thresholds, axes=axes)
    figure.colorbar(lc)

    axes.set_xlim([-0.05, 1.05])
    axes.set_ylim([-0.05, 1.05])

    axes.set_xlabel(fpr_label)
    axes.set_ylabel(tpr_label)

    axes.set_title(title)

    # axes.legend(loc="lower right")

    return figure, axes

def plotClassPerformance(y: pd.core.series.Series, prob_est: pd.core.frame.DataFrame, selClass:str=None, figsize=(10,5)):
    """Create plots associated to model classification performance based on output assigned probabilities.

    Args:
        y (pd.core.series.Series): Series containing true values of output 
        prob_est (pd.core.frame.DataFrame): Dataframe containing predicted categories probabilities of output
        selClass (str, optional): Positive class of the output. Defaults to None.
        figsize (Tuple[float, float], optional): Size of plot figures. Defaults to (10,5).
    """
    if selClass is None:
        try:
            selClass = y.cat.categories[1]
        except:
            selClass = y.unique()[0]
        warnings.warn('The first level of the output would be use as positive class', category=UserWarning)
    try:
        categories = y.cat.categories
    except:
        categories = y.unique()
        
    if len(categories) == 2:
        if not (prob_est.shape[1] == 1):
            try:
                prob_est = prob_est[:,y.cat.categories == selClass]
            except:
                prob_est = prob_est[:,y.unique() == selClass]
        # Calibration plot
        # Use cuts for setting the number of probability splits
        try:
            points_y, points_x = calibration_curve(y, prob_est, n_bins=10)
        except:
            points_y, points_x = calibration_curve(y.values, prob_est, pos_label=selClass, n_bins=10)
        fig, ax = plt.subplots(figsize=figsize)
        plt.plot(points_x, points_y, marker='o', linewidth=1, label='model')
        # reference line, legends, and axis labels
        line = mlines.Line2D([0, 1], [0, 1], color='black')
        transform = ax.transAxes
        line.set_transform(transform)
        ax.add_line(line)
        fig.suptitle('Plot 1/4: Calibration plot')
        ax.set_xlabel('Predicted probability')
        ax.set_ylabel('True probability in each bin')
        plt.show()
        
        selClassTitle = str(selClass)
        
        # Probability histograms
        try:
            output_name = y.name
        except:
            output_name = 'Output'
        df = pd.DataFrame(y, columns=[output_name])
        df['prob_est'] = prob_est
        sns.set(style ="ticks")
        d = {'color': ['r', 'b']}
        g = sns.FacetGrid(df, col=output_name, hue=output_name, hue_kws=d, 
                        margin_titles=True, 
                        height=figsize[1], 
                        aspect=figsize[0]/(2*figsize[1]))
        bins = np.linspace(0, 1, 10)
        g.map(plt.hist, "prob_est", bins=bins)
        plt.subplots_adjust(top=0.8)
        g.fig.suptitle('Plot 2/4: Probability of Class ' + selClassTitle) # can also get the figure from plt.gcf() 

        # calculate roc curve
        fpr, tpr, thresholds = mtrs.roc_curve(y, prob_est, pos_label=selClass)
        roc_auc = mtrs.auc(fpr, tpr)
        
        plot_roc(tpr, fpr, thresholds,
                subplots_kwargs={'figsize': figsize},
                title = 'Plot 3/4: ROC, Area under the ROC curve: ' + str(round(roc_auc,3)))

        y_true = y == selClass
        accuracy_scores = []
        for thresh in thresholds:
            accuracy_scores.append(mtrs.accuracy_score(y_true, [1 if m > thresh else 0 for m in prob_est]))
        
        accuracy_scores = np.array(accuracy_scores)

        _, ax = plt.subplots(figsize=figsize)
        ax.plot(thresholds, accuracy_scores, color='navy')
        ax.set_xlim([0.0, 1.0])
        ax.set_title('Plot 4/4: Accuracy across possible cutoffs')

def calibration_plot(real, estimations, figsize=(10,10)):
    """Calibration plot for each of the predictions created

    Args:
        real (pd.core.series.Series): Series containing true values of output
        estimations (pd.core.frame.DataFrame): Dataframe containing predicted values of output by models
        figsize (tuple): size of the figure. Defaults to (10, 10).
    """
    fig, ax = plt.subplots(figsize=figsize)
    for col in estimations.columns:
        try:
            y, x = calibration_curve(real, estimations.loc[:,col], n_bins=10)
        except:
            y, x = calibration_curve(real, estimations.loc[:,col], pos_label=real.cat.categories[1], n_bins=10)
        # only these two lines are calibration curves
        plt.plot(x, y, marker='o', linewidth=1, label=col)

        
    # reference line, legends, and axis labels
    line = mlines.Line2D([0, 1], [0, 1], color='black')
    transform = ax.transAxes
    line.set_transform(transform)
    ax.add_line(line)
    fig.suptitle('Calibration plot for Titanic data')
    ax.set_xlabel('Predicted probability')
    ax.set_ylabel('True probability in each bin')
    plt.legend()
    plt.show()

def roc_curve(real, estimations, selClass:str, figsize=(10,10), fpr_label='False Positive Rate', tpr_label='True Positive Rate', title='Receiver operating characteristic (ROC)'):
    """ROC plot for each of the predictions created

    Args:
        real (pd.core.series.Series): Series containing true values of  output
        estimations (pd.core.frame.DataFrame): Dataframe containing predicted values of output by models
        selClass (str): Positive class of the output
        figsize (tuple, optional): Size of figure. Defaults to (10, 10).
        fpr_label (str, optional): Label of fpr axis (x-axis). Defaults to 'False Positive Rate'.
        tpr_label (str, optional): Label of trp axis (y-axis). Defaults to 'True Positive Rate'.
        title (str, optional): title of ROC plot. Defaults to 'Receiver operating characteristic (ROC)'.
    """
    fig, ax = plt.subplots(figsize=figsize)
    for col in estimations.columns:
        fpr, tpr, thresholds = mtrs.roc_curve(real, estimations.loc[:,col], pos_label=selClass)
        # only these two lines are calibration curves
        ax.plot(fpr, tpr, linewidth=1, label=col)
        print('Area under the ROC curve of', col,':', round(mtrs.auc(fpr, tpr), 3))
    ax.plot((0, 1), (0, 1), '--', color='Gray')
    ax.set_xlim([-0.05, 1.05])
    ax.set_ylim([-0.05, 1.05])

    ax.set_xlabel(fpr_label)
    ax.set_ylabel(tpr_label)

    ax.set_title(title)

    ax.legend(loc="lower right")

def PlotDataframe(df, target):
        """
        Generate multiple subplots to visualize the relationships between the features in a dataframe and a specified output variable.
        This function is analogous to the a row in Seaborn's pairplot, but customized for handling both numeric and categorical data.

        Args:
            df (pd.core.frame.DataFrame): The dataframe containing the variables to plot. Each column is treated as a variable,
                                            and each row as an observation. The dataframe can contain both numeric and categorical data.
            target (str): The name of the target output column that will be used for comparison against the other columns in the dataframe.
                                The function will automatically adjust the plots based on whether this column is categorical or numeric.

        Behavior:
            - If the output variable (`output_name`) is categorical, it will be treated as a categorical feature.
            - The function dynamically generates subplots, where the number of plots corresponds to the number of features in the dataframe.
            - Depending on the type of data (categorical vs numeric), the function will plot different visualizations:
                - Categorical features: Bar plots and grouped bar charts.
                - Numeric features: Histograms, box plots, and regression plots.
            - For categorical output variables, bar plots are created to visualize the frequency of each category.
            - For numeric output variables, histograms or scatter plots with regression lines are used to examine relationships with other variables.
            - Plots are automatically laid out in a grid format.

        Example:
            PlotDataframe(df=my_dataframe, target='target')

        """
            # Identify if the target is categorical or numerical
        if pd.api.types.is_numeric_dtype(df[target]):
            target_type = 'numeric'
        else:
            target_type = 'categorical'
        
        # Number of features to plot
        features = [col for col in df.columns if col != target]
        n_features = len(features)
        
        # Create subplots: 2 plots per row
        fig, axes = plt.subplots(nrows=(n_features + 1) // 2, ncols=2, figsize=(14, 5 * ((n_features + 1) // 2)))
        axes = axes.flatten()  # Flatten in case of multi-dimensional axes
        
        for i, feature in enumerate(features):
            ax = axes[i]
            
            # Determine if the current feature is numeric or categorical
            if pd.api.types.is_numeric_dtype(df[feature]):
                # For numeric features
                if target_type == 'numeric':
                    sns.regplot(x=df[feature], y=df[target], ax=ax, scatter_kws={'alpha':0.5})
                    ax.set_title(f"Regression plot: {feature} vs {target}")
                else:
                    sns.boxplot(x=df[target], y=df[feature], ax=ax)
                    ax.set_title(f"Boxplot: {feature} by {target}")
            else:
                # For categorical features
                if target_type == 'numeric':
                    sns.boxplot(x=df[feature], y=df[target], ax=ax)
                    ax.set_title(f"Boxplot: {target} by {feature}")
                else:
                    sns.countplot(x=df[feature], hue=df[target], ax=ax)
                    ax.set_title(f"Countplot: {feature} by {target}")
        
        # Remove any unused axes
        for j in range(i + 1, len(axes)):
            fig.delaxes(axes[j])
    
        plt.tight_layout()
        plt.show()

def plotModelDiagnosis(df, pred, target):
        """
        Plot model diagnosis for regression analysis.
        
        This function generates diagnostic plots for regression analysis, including
        residual histograms and scatter plots or boxplots of residuals against each
        variable in the dataframe. For numerical variables, a scatter plot of residuals
        against the variable is created. For categorical variables,
        a boxplot of residuals against categories is created.
        
        Parameters
        ----------
        df : pd.core.frame.DataFrame
            Dataframe containing input, output, and prediction variables.
            
        pred : str
            Name of the column in `df` containing the model predictions.
            
        target : str
            Name of the column in `df` containing the actual output values.
        
        Returns
        -------
        None
            The function creates plots using Matplotlib and does not return any value.
        
        Examples
        --------
        >>> plotModelDiagnosis(df, 'predictions', 'actual_output')
        """
           # Calculate residuals
        df['residuals'] = df[target] - df[pred]
        
        # Set up the figure with subplots
        n_features = len(df.columns) - 2  # Exclude 'pred' and 'target' columns
        fig, axes = plt.subplots(nrows=(n_features + 1) // 2, ncols=2, figsize=(14, 5 * ((n_features + 1) // 2)))
        axes = axes.flatten()
    
        # Plot histogram of residuals
        sns.histplot(df['residuals'], bins=30, kde=True, ax=axes[0])
        axes[0].set_title('Histogram of Residuals')
        
        # Loop through each feature in df and plot residuals against it
        features = [col for col in df.columns if col not in [pred, target, 'residuals']]
        
        for i, feature in enumerate(features, 1):  # Start at 1 since the first plot is the histogram
            ax = axes[i]
            
            if pd.api.types.is_numeric_dtype(df[feature]):
                # Scatter plot for numeric variables
                sns.scatterplot(x=df[feature], y=df['residuals'], ax=ax, alpha=0.6)
                ax.set_title(f'Residuals vs {feature}')
                ax.axhline(0, color='red', linestyle='--')  # Horizontal line at 0 residual
            else:
                # Boxplot for categorical variables
                sns.boxplot(x=df[feature], y=df['residuals'], ax=ax)
                ax.set_title(f'Residuals vs {feature}')
                ax.axhline(0, color='red', linestyle='--')  # Horizontal line at 0 residual
        
        # Remove any extra empty subplots
        for j in range(i + 1, len(axes)):
            fig.delaxes(axes[j])
    
        plt.tight_layout()
        plt.show() 