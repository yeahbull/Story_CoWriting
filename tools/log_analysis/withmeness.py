import pandas as pd
import seaborn as sns
import numpy as np
import os

from scipy.stats import ttest_ind,ttest_rel

p = "LOG_P_CSV"
s = "LOG_S_CSV"
r = "LOG_R_CSV"

file_subject = "withmeness-11-stdout"

def counts(condition):
    all_vals = []
    sums = []
    for i in range(60):
        try:
            name = condition + '/' + str(i) + '/' + file_subject + ".log"
            table = pd.read_csv(name, dtype=str, names=['msg','_','time','type','value'])
        except IOError:
            try:
                name = condition + '/' + str(i) + '/' + file_subject + str(i) + ".log"
                table = pd.read_csv(name, dtype=str, names=['msg','_','time','type','value'])
            except IOError:
                continue

        table = table[table["type"]=="wmn_value"]
        vals = table['value']
        vals = pd.to_numeric(vals)
        vals = vals.as_matrix()[:550]
        time = table['time']
        time = pd.to_numeric(time)
        time = time.as_matrix()[:550]
        time -= time[0]

        all_vals.append(vals)
        sums.append(np.sum(vals))
    return np.stack(all_vals), np.array(sums)

all_vals_r,sums_r = counts(r)
all_vals_s,sums_s = counts(s)
all_vals_p,sums_p = counts(p)

print(ttest_ind(sums_p,sums_s))
print(ttest_ind(sums_p,sums_r))
print(ttest_ind(sums_s,sums_r))

sns.tsplot(all_vals_p,color='b')
sns.tsplot(all_vals_s,color='g')
sns.tsplot(all_vals_r,color='r')
sns.plt.show()
