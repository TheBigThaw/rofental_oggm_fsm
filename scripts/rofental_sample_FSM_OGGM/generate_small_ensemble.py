import pickle as pkl
import numpy as np
import pandas as pd

with open('stats_analysis_489.pkl','rb') as f:
     Q = pkl.load(f)
     f.close()

ens_size = 15

mask_high = np.where(Q['eigenvalues']>.003)[0]

rand_sample = np.random.randn(15,len(mask_high)) * Q['eigenvalues'][mask_high]

eigenvec_high = Q['eigenvectors'][:,mask_high]

perturb_ensemble = np.matmul(eigenvec_high,rand_sample.T)

ensemble = Q['mean'][:,None] + perturb_ensemble

df = pd.DataFrame(data=ensemble.T,columns=Q['param_names'],index=None)

df.to_csv('ensemble.csv',index=False)
