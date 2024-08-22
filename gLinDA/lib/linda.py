import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import statsmodels.stats.multitest as mult
import math
import scipy as sp
from io import StringIO

from gLinDA.lib.errors import LindaInternalError, LindaWrongData

__author__ = "Leon Fehse, Mohammad Tajabadi, Roman Martin"
__credits__ = "Heinrich Heine University Düsseldorf"


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

    @staticmethod
    def bw_nrd0(x): # https://stackoverflow.com/questions/45193294/show-more-significant-figures-of-coefficients
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
    def windsor_dedup(P, Y, quan):
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
        return P, Y

    @staticmethod
    def winsor_fun(Y, quan, feature_dat_type):
        if feature_dat_type == "count":
            N = Y.sum(axis=0)
            P = Y.T.divide(N, axis=0).T
            P, Y = LinDA.windsor_dedup(P, Y, quan)
            Y = round(P.T.multiply(N, axis=0).T).astype(int)
        elif feature_dat_type == "proportion":
            X, Y = LinDA.windsor_dedup(Y, Y, quan)

        return Y

    @staticmethod
    def read_table(path: str, col: str = "") -> pd.DataFrame:
        if len(col):
            try:
                table: pd.DataFrame = pd.read_csv(path, index_col=col)
            except ValueError as e:
                print(e)
                raise LindaWrongData("Error: Probably wrong index, please verify if the column %s exists in the file %s"
                                     % (col, path))
            return table
        else:
            for col in ["ID", "id", "SampleID", "Sample", "sample", "sample_name"]:
                try:
                    table: pd.DataFrame = pd.read_csv(path, index_col=col)
                    return table
                except ValueError:
                    continue

        raise ValueError("Could not identify the index columns for %s" % path)

    @staticmethod
    def split_formula(formula: str):
        all_var_formula = formula
        for delim in ["+", "~"]:
            all_var_formula = " ".join(all_var_formula.split(delim))
        return all_var_formula.split()

    @staticmethod
    def correct_bias(n: int, formula: str, coefficients: dict):
        all_var = LinDA.split_formula(formula)

        for key, df in coefficients.items():
            pre_bias, iters = LinDA.default_mean_shift_modeest(math.sqrt(float(n)) * df["stat"])
            bias = pre_bias / math.sqrt(float(n))
            df["stat"] -= bias
            df["stat"] /= df["stde"]

        dof = n - (len(all_var) + 1)
        return coefficients, dof

    @staticmethod
    def linda_pvalues(stats, dof):
        pval = 2 * sp.stats.t.cdf(-abs(stats), df=dof)
        reject, padj = mult.fdrcorrection(pval)
        return pval, reject, padj

    @staticmethod
    def linda_output(dof, coefficients):
        output_frames = {}
        variables = []
        for voi in coefficients.keys():
            pval, reject, padj = LinDA.linda_pvalues(coefficients[voi]["stat"], dof)
            output = pd.DataFrame({
                "base_mean": coefficients[voi]["base_mean"],
                "stat": coefficients[voi]["stat"],
                "stde": coefficients[voi]["stde"],
                "pval": pval,
                "padj": padj,
                "reject": reject})
            output.index = coefficients[voi].index
            output_frames[voi] = output
            variables.append(voi)

        return output_frames

    @staticmethod
    def take_avg_params(all_parameters: dict, union: bool = True):
        models_list = []
        weights = []
        bias_list = []
        id_list = []

        for id_, linda_params in all_parameters.items():
            model = linda_params["coefs"]
            biases = linda_params["biases"]
            id_list.append(id_)
            weight = linda_params["size"]
            models_list.append(model)
            weights.append(weight)
            bias_list.append(biases)

        all_taxa = set()
        if union:
            for model in models_list:
                for voi in model:
                    all_taxa.update(model[voi].index)
        else:  
        
            all_taxa = set(models_list[0][next(iter(models_list[0]))].index)

            for dict in models_list[1:]:
                indexes = set(dict[next(iter(dict))].index)
                all_taxa.intersection_update(indexes)
                     
        all_taxa_list = list(all_taxa)
        all_taxa_list = sorted(all_taxa_list)

        covs = list(models_list[0].keys())
        columns_list = models_list[0][covs[0]].columns

        final_dict = {voi: pd.DataFrame(columns=columns_list, index=all_taxa_list) for voi in covs}

        # checking averages
        for voi in covs:
            for taxa in all_taxa_list:
                total_weighted_sum = 0
                total_weight = 0
                weighted_sums = {}
                for i, model in enumerate(models_list):
                    if voi in model and taxa in model[voi].index:
                        taxa_sums = model[voi].loc[taxa]["taxa_sums"]
                        for col in model[voi].columns:
                            if col not in weighted_sums:
                                weighted_sums[col] = 0
                            if col == "stde" or col == "stde_avg":
                                weighted_sums[col] += (model[voi].loc[taxa][col] * weights[i]) ** 2

                            else:
                                weighted_sums[col] += model[voi].loc[taxa][col] * weights[i]

                        total_weight += weights[i]
                for col in weighted_sums:
                    if col == "stde" or col == "stde_avg":
                        final_dict[voi].loc[taxa, col] = np.sqrt(weighted_sums[col]) / total_weight
                    else:
                        final_dict[voi].loc[taxa, col] = weighted_sums[col] / total_weight

            final_dict[voi] = final_dict[voi].astype(float)

            # TODO: Arsam, please check this
            temp = final_dict[voi]
            if ("stde_avg" in temp.columns):
                temp["division"] = temp["stat"] / temp["stde_avg"]
            else:
                temp["division"] = temp["stat"] / temp["stde"]

        return final_dict

    @staticmethod
    def linda_coefficients(
            feature_data: pd.DataFrame,
            meta_data: pd.DataFrame,
            formula: str,
            feature_dat_type: str = "count",
            data_name: str = "",
            prev_filter: float = 0.0,
            mean_abund_filter: float = 0.0,
            max_abund_filter: float = 0.0,
            is_winsor: bool = True,
            outlier_pct: float = 0.03,
            adaptive: bool = True,
            zero_handling: str = "pseudo_count",
            pseudo_count: float = 0.5,
            corr_cut: float = 0.1,
            verbose: bool = False,
            local: bool = True):

        return_bucket: dict = {"W": None, "Z": None}
        if feature_data.isnull().values.any():
            raise Exception("The feature table contains NAs! Please remove!\n")
        delims = ["+", "~"]
        all_var_formula = formula
        for delim in delims:
            all_var_formula = " ".join(all_var_formula.split(delim))
        all_var = all_var_formula.split()

        Z = meta_data.loc[:, all_var]

        # Filter sample
        keep_sam = Z.notna().all(axis=1)
        Z = Z[keep_sam]

        try:
            Y = feature_data.T[keep_sam].T
        except Exception:
            raise Exception("Error: Probably you have to transpose the feature table (you can do transpose it in the "
                            "configuration file)")
        Z.columns = all_var

        # Filter features
        temp = Y.T.divide(Y.sum(axis=0), axis=0).T
        keep_tax = (((temp != 0).mean(axis=1) >= prev_filter) & (temp.mean(axis=1) >= mean_abund_filter) & (
                temp.max(axis=1) >= max_abund_filter))

        if verbose:
            numfiltered_out = len(Y.index) - sum(keep_tax)
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
            n = len(Y.columns)

        if verbose:
            print(f"The filtered data has {n} samples and {m} features will be tested")

        if sum((Y != 0).sum(axis=1) <= 2) != 0:
            print("Some features have less than 3 nonzero values!\n They have virtually no statistical power.\n"
                  "You may consider filtering them in the analysis!")

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

        if not list(feature_data.index.values):
            taxa_name = pd.Series([i for i in range(0, int(len(feature_data)))])[keep_tax.values]
        else:
            taxa_name = feature_data.index.values[keep_tax.values]
        if not list(meta_data.index.values):
            samp_name = [i for i in range(0, int(len(meta_data)))][keep_sam.values]
        else:
            samp_name = meta_data.index.values[keep_sam.values]

        # zero handling
        if feature_dat_type == "count":
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

        # CLR transform
        logY = np.log2(Y)
        W = logY - logY.mean(axis=0)
        W = W.T
        W = W.apply(pd.to_numeric)

        return_bucket.update({"W": W, "Z": Z})
        normalized_data = feature_data.div(feature_data.sum(axis=0), axis=1)
        sums_normalized = normalized_data.sum(axis=1)

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
                model_summary = model.summary2().tables[1]  # .as_html()
                frames.append(model_summary)

            res = pd.concat(frames)
        else:
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

        res_intc = res[res.index == "Intercept"]
        base_mean = 2 ** res_intc["Coef."].values
        base_mean = base_mean / np.sum(base_mean) * 1e6
        intercept = res_intc["Coef."].values
        output_frames = {}
        biases = {}
        stat_dict = {}

        for voi in list(set(res.index.values)):

            if voi == "Intercept":
                continue

            res_voi = res[res.index == voi]
            res_voi.reset_index(inplace=True, drop=True)

            log2FoldChange = res_voi["Coef."]
            lfcSE = res_voi["Std.Err."]

            highdec_log2FoldChange = []
            for val in log2FoldChange:
                val = "{0:.16f}".format(val)
                highdec_log2FoldChange.append(float(val))

            highdec_log2FoldChange = np.array(highdec_log2FoldChange, dtype="float64")
            pre_bias, iters = LinDA.default_mean_shift_modeest(math.sqrt(float(n)) * highdec_log2FoldChange)
            bias = pre_bias / math.sqrt(n)

            sums_normalized_filtered = sums_normalized[sums_normalized.index.isin(taxa_name)].values

            output = pd.DataFrame({"base_mean": base_mean,
                                   "intercept": intercept,
                                   "stat": highdec_log2FoldChange,
                                   "stde": lfcSE,
                                   "taxa_sums": sums_normalized_filtered,
                                   })

            output.index = taxa_name

            biases[voi] = bias
            stat_dict[voi] = output
            output_frames[voi] = output

        if local:
            return stat_dict
        else:
            return {
                "coefs": stat_dict,
                "biases": biases,
                "formula": formula,
                "size": len(meta_data)
            }

    @staticmethod
    def run(feature, meta, cfg: dict, local: bool = True):
        try:
            return LinDA.linda_coefficients(
                feature_data=feature,
                meta_data=meta,
                feature_dat_type=cfg["feature_type"],
                data_name="name",
                formula=cfg["formula"],
                prev_filter=cfg["prevalence"],
                mean_abund_filter=cfg["mean_abundance"],
                max_abund_filter=cfg["max_abundance"],
                is_winsor=cfg["winsor"],
                outlier_pct=cfg["outlier_percentage"],
                adaptive=cfg["adaptive"],
                zero_handling=cfg["zero_handling"],
                pseudo_count=cfg["pseudo_count"],
                corr_cut=cfg["correction_cutoff"],
                verbose=cfg["verbose"],
                local=local
            )
        except Exception as e:
            raise LindaInternalError(e)

    @staticmethod
    def run_local(cfg):
        results = {}
        try:
            feature_data = LinDA.read_table(cfg["feature_table"], cfg["feature_index"])
            if cfg["feature_transpose"]:
                feature_data = feature_data.T
            meta_data = LinDA.read_table(cfg["meta_table"], cfg["meta_index"])
            coefficients = LinDA.run(feature_data, meta_data, cfg, True)
            corrected_coefficients, dof = LinDA.correct_bias(len(meta_data), cfg["formula"], coefficients)
            results = LinDA.linda_output(dof, corrected_coefficients)
        except LindaWrongData as e:
            print(e)
        except LindaInternalError as e:
            print(e)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(e)
        finally:
            return results

    @staticmethod
    def run_sl(cfg):
        feature_data = LinDA.read_table(cfg["feature_table"], cfg["feature_index"])
        if cfg["feature_transpose"]:
            feature_data = feature_data.T
        meta_data = LinDA.read_table(cfg["meta_table"], cfg["meta_index"])
        return LinDA.run(feature_data, meta_data, cfg, False)

    @staticmethod
    def run_sl_avg(all_parameters: dict, formula: str, union: bool = True):
        results = {}
        try:
            total_data_size = sum([a["size"] for a in all_parameters.values()])
            merged_coefficients = LinDA.take_avg_params(all_parameters)
            corrected_coefficients, dof = LinDA.correct_bias(total_data_size, formula, merged_coefficients)
            results = LinDA.linda_output(dof, corrected_coefficients)
        except LindaWrongData as e:
            print(e)
        except LindaInternalError as e:
            print(e)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(e)
            raise LindaInternalError(e)
        finally:
            return results

    @staticmethod
    def display_results(results: dict):
        collector: str = ""
        for key, item in results.items():
            try:
                if len(item):
                    new_tab: pd.DataFrame = item[item["reject"] == True].sort_values(by=["padj"])
                    collector += "%s (%d)\r\n" % (key, len(new_tab))
                    if len(new_tab):
                        collector += "%s\r\n" % new_tab.drop(["reject"], axis=1).to_string()
                    else:
                        collector += "Sorry, no significant match\r\n"
                    collector += "\r\n"
            except Exception as e:
                print(e)
                continue
        return collector
