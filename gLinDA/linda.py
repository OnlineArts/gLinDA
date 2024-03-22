#!/bin/env python3
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import statsmodels.stats.multitest as mult
import math
import scipy as sp
from io import StringIO


class LinDA:

    @staticmethod
    def default_shorth(x):
        ny = len(x)
        k = math.ceil(ny / 2) - 1
        y = sorted(x)
        inf = y[:(ny - k)]
        sup = y[k:]
        diffs = np.array(sup) - np.array(inf)
        i = np.where(diffs == min(diffs))
        if len(i[0]) > 1:
            i = math.floor(np.mean(i[0]))
        else:
            i = i[0][0]
        M = np.mean(y[i:(i + k + 1)])
        return M

    # function not by me found this here: https://stackoverflow.com/questions/45193294/show-more-significant-figures-of-coefficients
    @staticmethod
    def bw_nrd0(x):

        if len(x) < 2:
            raise (Exception("need at least 2 data points"))

        hi = np.std(x, ddof=1)
        q75, q25 = np.percentile(x, [75, 25])
        iqr = q75 - q25
        lo = min(hi, iqr / 1.34)

        lo = lo or hi or abs(x[0]) or 1

        return 0.9 * lo * len(x) ** -0.2

    @staticmethod
    def default_mean_shift_modeest(x):
        par = LinDA.default_shorth(x)
        bw = LinDA.bw_nrd0(x)
        tolerance = math.sqrt(np.finfo(float).eps)
        iter = 1000
        s = 0
        for j in range(iter):
            z = (x - par) / bw
            k = sp.stats.norm.pdf(z)
            M = np.dot(x, k) / np.sum(k)
            th = abs(M / par - 1)
            if th < tolerance:
                s = j
                break
            par = M
        return par, s + 1

    @staticmethod
    def winsor_fun(Y, quan, feature_dat_type):
        if feature_dat_type == 'count':
            N = Y.sum(axis=0)
            P = Y.T.divide(N, axis=0).T
            cut = P.quantile(q=quan, axis=1)
            empty_arr = np.empty((len(Y.index.values), len(Y.columns.values)))
            for row, cutval in zip(empty_arr, cut):
                row.fill(cutval)
            ind = P > empty_arr
            temp = np.where(ind)
            cols = temp[1]
            rows = temp[0]
            for row_i, col_j in zip(rows, cols):
                P.iloc[row_i, col_j] = empty_arr[row_i, col_j]
            Y = round(P.T.multiply(N, axis=0).T).astype(int)

        if feature_dat_type == 'proportion':
            cut = Y.quantile(q=quan, axis=1)
            empty_arr = np.empty((len(Y.index.values), len(Y.columns.values)))
            for row, cutval in zip(empty_arr, cut):
                row.fill(cutval)
            ind = Y > empty_arr
            temp = np.where(ind)
            cols = temp[1]
            rows = temp[0]
            for row_i, col_j in zip(rows, cols):
                Y.iloc[row_i, col_j] = empty_arr[row_i, col_j]

        return Y

    @staticmethod
    def trans_linda(feature_dat, meta_dat, formula,
                    feature_dat_type='count', data_name="", model_output_path="", prev_filter: float = 0.0,
                    mean_abund_filter=0, max_abund_filter=0, is_winsor=True,
                    outlier_pct=0.03, adaptive=True, zero_handling='pseudo_count',
                    pseudo_count=0.5, corr_cut=0.1, p_adj_method='BH',
                    alpha=0.05, n_cores=1, verbose=True):

        if feature_dat.isnull().values.any():
            raise Exception("The feature table contains NAs! Please remove!\n")
        delims = ["+", "~"]
        all_var_formula = formula
        for delim in delims:
            all_var_formula = " ".join(all_var_formula.split(delim))
        all_var = all_var_formula.split()
        Z = meta_dat.loc[:, all_var]

        ##############################################################################
        # Filter sample
        keep_sam = Z.notna().all(axis=1)
        Z = Z[keep_sam]
        Y = feature_dat.T[keep_sam].T
        Z.columns = all_var

        # Filter features
        temp = Y.T.divide(Y.sum(axis=0), axis=0).T
        keep_tax = (((temp != 0).mean(axis=1) >= prev_filter) & (temp.mean(axis=1) >= mean_abund_filter) & (
                    temp.max(axis=1) >= max_abund_filter))
        if verbose:
            numfiltered_out = len(Y.index) - sum(keep_tax)
            num_kept = sum(keep_tax)
            print(f"{numfiltered_out} features are filtered!")
        Y = Y[keep_tax]
        n = len(Y.columns.values)
        m = len(Y.index.values)

        if (Y.sum(axis=0) == 0).any():
            ind = Y.sum(axis=0) == 0
            Y = Y[ind]
            Z = Z[ind]
            Z.columns = all_var
            keep_sam = keep_sam[ind]
            n = len(Y.colu)

        if verbose:
            print(f"The filtered data has {n} samples and {m} features will be tested")

        if sum((Y != 0).sum(axis=1) <= 2) != 0:
            print(
                "'Some features have less than 3 nonzero values!\nThey have virtually no statistical power. You may consider filtering them in the analysis!")

        ###############################################################################
        # scaling numerical variables
        ind = [i for i in Z.columns.values if np.issubdtype(Z[i].dtype, np.number)]
        Z[ind] = (Z[ind] - Z[ind].mean()) / Z[ind].std()

        # winsorization
        if is_winsor:
            Y = LinDA.winsor_fun(Y, 1 - outlier_pct, feature_dat_type)

        # random effects present
        if "(" in formula:
            random_effect = True
        else:
            random_effect = False

        #
        if not list(feature_dat.index.values):
            taxa_name = pd.Series([i for i in range(0, int(len(feature_dat)))])[keep_tax.values]
        else:
            taxa_name = feature_dat.index.values[keep_tax.values]
        if not list(meta_dat.index.values):
            samp_name = [i for i in range(0, int(len(meta_dat)))][keep_sam.values]
        else:
            samp_name = meta_dat.index.values[keep_sam.values]

        ##############################################################################
        # zero handling
        if feature_dat_type == 'count':
            if (Y == 0).any().any():
                N = Y.sum(axis=0)
                if adaptive:
                    logN = np.log(N)
                    if random_effect:
                        tmp_model = smf.mixedlm(formula="logN" + formula, data=Z)
                        tmp = tmp_model.fit()
                    else:
                        tmp_model = smf.ols(formula="logN " + formula, data=Z)
                        tmp = tmp_model.fit()
                    summary_as_csv = tmp.summary().tables[1].as_html()
                    tmp_summary = pd.read_html(StringIO(str(summary_as_csv)), header=0, index_col=0)[0]
                    corr_pval = tmp_summary["P>|t|"][1:]
                    if (corr_pval <= corr_cut).any():
                        if verbose:
                            print("Imputation approach is used.")
                        zero_handling = "Imputation"
                    else:
                        if verbose:
                            print("Pseudo-count approach is used.")
                        zero_handling = "Pseudo-count"
                if zero_handling == "Imputation":
                    N_mat = np.empty(shape=(len(N.index), m))
                    for row, N_val in zip(N_mat, N):
                        row.fill(N_val)
                    N_mat = N_mat.T
                    N_mat[Y > 0] = 0
                    tmp = N[np.argmax(N_mat, axis=1)]
                    Y = Y + (N_mat.T / tmp.values).T
                else:
                    Y = Y + pseudo_count

        if feature_dat_type == "proportion":
            if (Y == 0).any().any():
                half_min = Y[Y != 0].min().min() * 0.5
                Y[Y == 0] = half_min
                Y.columns = samp_name
                Y.index = taxa_name

        ##############################################################################
        # CLR transform
        logY = np.log2(Y)
        W = logY - logY.mean(axis=0)
        W = W.T
        W = W.apply(pd.to_numeric)

        ##############################################################################
        # model fitting
        if not random_effect:
            if verbose:
                print("Fit linear models ...")
            frames = []
            models = {}
            for col in W.columns.values:
                Wcol = W[col]
                model = smf.ols(formula="Wcol " + formula, data=Z).fit()
                model_name = str(col) + "_taxon_model_" + data_name + ".pickle"
                models[model_name] = model
                # print(model.summary2().tables[1])
                model_summary = model.summary2().tables[1]  # .as_html()
                # model_summary = pd.read_html(StringIO(str(summary_as_csv)), header=0, index_col=0)[0]
                frames.append(model_summary)
            dof = n - (len(all_var) + 1)
            res = pd.concat(frames)
        else:  # needs to be checked still
            if verbose:
                print("Fit linear mixed effect models ...")
            frames = []
            models = {}
            for col in W.columns.values:
                Wcol = W[col]
                model = smf.mixedlm(formula="Wcol " + formula, data=Z).fit()
                model_name = str(col) + "_taxon_model_" + data_name + ".csv"
                models[model_name] = model
                summary_as_csv = model.summary().tables[1].as_html()
                model_summary = pd.read_html(StringIO(str(summary_as_csv)), header=0, index_col=0)[0]
                frames.append(model_summary)
            res = pd.concat(frames)
            dof = res[:, 2]

        ##############################################################################
        # save models
        for name, mod in models.items():
            if model_output_path != "" and model_output_path[-1] != "/":
                full_path = model_output_path + "/" + name
            else:
                full_path = model_output_path + name
            mod.save(full_path)

        res_intc = res[res.index == "Intercept"]
        base_mean = 2 ** res_intc["Coef."].values
        base_mean = base_mean / np.sum(base_mean) * 1e6

        ##############################################################################
        # calculate and adjust pvalues and create output
        output_frames = {}
        biases = {}
        variables = []
        for voi in list(set(res.index.values)):
            if voi == "Intercept":
                continue
            res_voi = res[res.index == voi]
            res_voi.reset_index(inplace=True, drop=True)
            log2FoldChange = res_voi["Coef."]
            lfcSE = res_voi["Std.Err."]
            highdec_log2FoldChange = []
            for val in log2FoldChange:
                val = '{0:.16f}'.format(val)
                highdec_log2FoldChange.append(float(val))
            highdec_log2FoldChange = np.array(highdec_log2FoldChange, dtype="float64")
            pre_bias, iters = LinDA.default_mean_shift_modeest(math.sqrt(float(n)) * highdec_log2FoldChange)
            bias = pre_bias / math.sqrt(n)
            highdec_log2FoldChange = highdec_log2FoldChange - bias
            stat = highdec_log2FoldChange / lfcSE
            pval = 2 * sp.stats.t.cdf(-abs(stat), df=dof)
            reject, padj = mult.fdrcorrection(pval)
            df = [dof for i in range(m)]
            log2FoldChange = highdec_log2FoldChange
            output = pd.DataFrame({"base_mean": base_mean,
                                   "log2FoldChange": log2FoldChange,
                                   "lfcSE": lfcSE,
                                   "stat": stat,
                                   "pval": pval,
                                   "padj": padj,
                                   "reject": reject,
                                   "df": df})
            output.index = taxa_name
            output_frames[voi] = output
            biases[voi] = bias
            variables.append(voi)
        if verbose:
            print("Completed.")

        return {"variables": variables, "biases": biases, "output": output_frames, "feature_data_used": Y,
                "meta_data_used": Z}

    @staticmethod
    def read_table(path: str, col: str) -> pd.DataFrame:
        table: pd.DataFrame = pd.read_csv(path, index_col=col)
        return table

    def __init__(self, feature_table: str, metadata_table: str, formula: str, model_path: str, data_name: str,
                 prev_filter: float, mean_abundance_filter: int, max_abundance_filter: int, feature_type: str,
                 outlier_pct: float, alpha: float, winsor: bool):
        self._results = LinDA.trans_linda(LinDA.read_table(feature_table, "ID"),
                                          LinDA.read_table(metadata_table, "SampleID"),
                                          formula,
                                          feature_type,
                                          data_name,
                                          model_path,
                                          prev_filter,
                                          mean_abundance_filter,
                                          max_abundance_filter,
                                          winsor,
                                          outlier_pct,
                                          True,
                                          "pseudo_count",
                                          0.5,
                                          0.1,
                                          "BH",
                                          alpha,
                                          1,
                                          True,
                                          )

    def get_results(self):
        return self._results