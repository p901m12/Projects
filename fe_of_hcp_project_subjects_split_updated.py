# -*- coding: utf-8 -*-
"""FE_of_HCP_project_subjects_split_updated.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1IWbOZ9q54yExvK-D5iDPP306cutX-wwL

# Setup
"""

# @title Install dependencies
!pip install pandas --quiet
!pip install seaborn --quiet
!pip install nilearn --quiet

import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from nilearn import plotting, datasets

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import train_test_split
from sklearn.datasets import make_classification
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from sklearn.metrics import accuracy_score

# Commented out IPython magic to ensure Python compatibility.
# @title Figure settings
# %matplotlib inline
# %config InlineBackend.figure_format = 'retina'
plt.style.use("https://raw.githubusercontent.com/NeuromatchAcademy/course-content/main/nma.mplstyle")

"""# Download and extract the data"""

## The download cells will store the data in nested directories starting here:
HCP_DIR = "./hcp"
if not os.path.isdir(HCP_DIR):
  os.mkdir(HCP_DIR)

# The data shared for NMA projects is a subset of the full HCP dataset
N_SUBJECTS = 339

# The data have already been aggregated into ROIs from the Glasser parcellation
N_PARCELS = 360

# The acquisition parameters for all tasks were identical
TR = 0.72  # Time resolution, in seconds

# The parcels are matched across hemispheres with the same order
HEMIS = ["Right", "Left"]

# Each experiment was repeated twice in each subject
N_RUNS = 2

# There are 7 tasks. Each has a number of 'conditions'

EXPERIMENTS = {
    'MOTOR'      : {'runs': [5,6],   'cond':['lf','rf','lh','rh','t','cue']},
    'WM'         : {'runs': [7,8],   'cond':['0bk_body','0bk_faces','0bk_places','0bk_tools','2bk_body','2bk_faces','2bk_places','2bk_tools']},
    'EMOTION'    : {'runs': [9,10],  'cond':['fear','neut']},
    'GAMBLING'   : {'runs': [11,12], 'cond':['loss','win']},
    'LANGUAGE'   : {'runs': [13,14], 'cond':['math','story']},
    'RELATIONAL' : {'runs': [15,16], 'cond':['match','relation']},
    'SOCIAL'     : {'runs': [17,18], 'cond':['mental','rnd']}
}

# You may want to limit the subjects used during code development.
# This will use all subjects:
subjects = range(N_SUBJECTS)

import os, requests, tarfile
fname = "hcp_task.tgz"
url = "https://osf.io/s4h8j/download/"

if not os.path.isfile(fname):
  try:
    r = requests.get(url)
  except requests.ConnectionError:
    print("!!! Failed to download data !!!")
  else:
    if r.status_code != requests.codes.ok:
      print("!!! Failed to download data !!!")
    else:
      print(f"Downloading {fname}...")
      with open(fname, "wb") as fid:
        fid.write(r.content)
      print(f"Download {fname} completed!")

fname_ex = "hcp_task"
path_name = os.path.join(HCP_DIR, fname_ex)
if not os.path.exists(path_name):
  print(f"Extracting {fname_ex}.tgz...")
  with tarfile.open(f"{fname_ex}.tgz") as fzip:
    fzip.extractall(HCP_DIR)
else:
  print(f"File {fname_ex}.tgz has already been extracted.")

regions = np.load(os.path.join(HCP_DIR, "hcp_task", "regions.npy")).T
region_info = dict(name=regions[0].tolist(),
                   network=regions[1],
                   hemi=['Right']*int(N_PARCELS/2) + ['Left']*int(N_PARCELS/2))

"""# Load the data"""

def load_single_timeseries(subject, experiment, run, dir, remove_mean=True):
  """Load timeseries data for a single subject and single run.

  Args:
    subject (int): 0-based subject ID to load
    experiment (str): Name of experiment
    run (int): 0-based run index, across all tasks
    remove_mean (bool): If True, subtract the parcel-wise mean (typically the mean BOLD signal is not of interest)

  Returns
    ts (n_parcel x n_timepoint array): Array of BOLD data values

  """
  bold_run = EXPERIMENTS[experiment]['runs'][run]
  bold_path = os.path.join(dir, "subjects", str(subject), "timeseries")
  bold_file = f"bold{bold_run}_Atlas_MSMAll_Glasser360Cortical.npy"
  ts = np.load(os.path.join(bold_path, bold_file))
  if remove_mean:
    ts -= ts.mean(axis=1, keepdims=True)
  return ts


def load_evs(subject, experiment, run, dir):
  """Load EVs (explanatory variables) data for one task experiment.

  Args:
    subject (int): 0-based subject ID to load
    experiment (str) : Name of experiment
    run (int) : 0-based run index, across all tasks

  Returns
    evs (list of lists): A list of frames associated with each condition

  """
  frames_list = []
  task_key = 'tfMRI_' + experiment + '_' + ['RL', 'LR'][run]
  for cond in EXPERIMENTS[experiment]['cond']:
    ev_file = os.path.join(dir, "subjects", str(subject), "EVs",
                           str(task_key), f"{cond}.txt")

    ev_array = np.loadtxt(ev_file, ndmin=2, unpack=True)
    ev = dict(zip(["onset", "duration", "amplitude"], ev_array))
    # Determine when trial starts, rounded down
    start = np.floor(ev["onset"] / TR).astype(int)
    # Use trial duration to determine how many frames to include for trial
    duration = np.ceil(ev["duration"] / TR).astype(int)
    # Take the range of frames that correspond to this specific trial
    frames = [s + np.arange(0, d) for s, d in zip(start, duration)]
    frames_list.append(frames)

  return frames_list

my_exp = 'WM'
my_subj = subjects[8]
my_run = 1

data = load_single_timeseries(subject=my_subj,
                              experiment=my_exp,
                              run=my_run,
                              dir=os.path.join(HCP_DIR, "hcp_task"),
                              remove_mean=True)
print(data.shape)

evs = load_evs(subject=my_subj, experiment=my_exp,run=my_run, dir=os.path.join(HCP_DIR, "hcp_task"))

# MEAN VERSION

def average_frames(data, evs, experiment, cond):
    idx = EXPERIMENTS[experiment]['cond'].index(cond)
    return np.array([np.mean(data[:, evs[idx][i]], axis=1, keepdims=True) for i in range(len(evs[idx]))]).reshape((360,))

X_mean_act, y_mean_act = [], []
my_exp = 'WM'
my_dir = os.path.join(HCP_DIR, "hcp_task")
my_conditions = ['body','faces','places','tools']
for my_subj in range(N_SUBJECTS):
  for my_run in range(N_RUNS):
    evs = load_evs(subject=my_subj, experiment=my_exp,run=my_run, dir=my_dir)
    for cond in my_conditions:
      zerobk_activity = average_frames(data, evs, my_exp, f'0bk_{cond}')
      twobk_activity = average_frames(data, evs, my_exp, f'2bk_{cond}')
      X_mean_act.append({'subject': my_subj, 'condition': cond, 'run': my_run, 'activity':zerobk_activity, })
      X_mean_act.append({'subject': my_subj, 'condition': cond, 'run': my_run, 'activity':twobk_activity, })
      y_mean_act.append('0bk')
      y_mean_act.append('2bk')
X_mean_act = np.vstack(pd.DataFrame.from_dict(X_mean_act).to_numpy()[:, -1])
y_mean_act = np.vstack(pd.DataFrame.from_dict(y_mean_act).to_numpy()).reshape(-1)

X_mean_act.shape

y_mean_act

#@ MAXiMUM VERSION
def maximum_frames(data, evs, experiment, cond):
    idx = EXPERIMENTS[experiment]['cond'].index(cond)
    return np.array([np.max(data[:, evs[idx][i]], axis=1, keepdims=True) for i in range(len(evs[idx]))]).reshape((360,))

X_max_act, y_max_act = [], []
my_exp = 'WM'
my_dir = os.path.join(HCP_DIR, "hcp_task")
my_conditions = ['body','faces','places','tools']
for my_subj in range(N_SUBJECTS):
  for my_run in range(N_RUNS):
    evs = load_evs(subject=my_subj, experiment=my_exp,run=my_run, dir=my_dir)
    for cond in my_conditions:
      zerobk_activity = average_frames(data, evs, my_exp, f'0bk_{cond}')
      twobk_activity = average_frames(data, evs, my_exp, f'2bk_{cond}')
      X_max_act.append({'subject': my_subj, 'condition': cond, 'run': my_run, 'activity':zerobk_activity, })
      X_max_act.append({'subject': my_subj, 'condition': cond, 'run': my_run, 'activity':twobk_activity, })
      y_max_act.append(0)
      y_max_act.append(1)
# y_max_act = np.vstack(pd.DataFrame.from_dict(y_max_act).to_numpy()).reshape(-1)
y = np.array(y_max_act).astype(int)
X_df = pd.DataFrame.from_dict(X_max_act)

"""# Split X, y into train and test"""

subjects_idx = X_df['subject'].unique()
test_size = N_SUBJECTS // 10
test_subj_idx = np.random.choice(subjects_idx, size=test_size, replace=False)

selected_subj =  X_df[X_df['subject'].isin(test_subj_idx)]
test_indices = selected_subj.index.values
X_test = X_df.iloc[test_indices]
y_test = y[test_indices]

X_train = X_df.iloc[~X_df.index.isin(test_indices)]
train_indices = X_train.index.values
y_train = y[train_indices]

X_test

"""# Feature selection"""

X_test = np.vstack(X_test.to_numpy()[:, -1])
X_test.shape

X_train = np.vstack(X_train.to_numpy()[:, -1])
X_train.shape

"""# Modeling: LogisticRegression"""

# model fitting
model = LogisticRegression(penalty = 'l2', solver='liblinear', random_state=0).fit(X_train, y_train)

#predict
yhats = model.predict(X_test)

# compare train vs test
model.score(X_test, y_test, sample_weight=None)

"""## Confusion matrix & Classification report"""

from sklearn.metrics import confusion_matrix, classification_report
cm = confusion_matrix(y_test, yhats, labels=None, sample_weight=None, normalize=None)
cr = classification_report(y_test, yhats, labels=None, target_names=['class 0', 'class 1'], sample_weight=None, digits=2, output_dict=False, zero_division='warn')
print(cr)

disp = ConfusionMatrixDisplay(confusion_matrix=cm)
disp.plot()
plt.xticks((0,1),('0_back', '2_back'))
plt.yticks((0,1),('0_back', '2_back'))
plt.show()

"""## Accuracy test"""

accuracy_score(y_test, yhats, normalize=True)

"""# Individual conditions accuracy"""

#oguls code
for cond in my_conditions:

  X_cond = X_df.iloc[test_indices]['condition'] == cond
  X_cond = X_cond.to_numpy()
  yhats_cond = model.predict(X_test[X_cond])

  cm_cond = confusion_matrix(y_test[X_cond], yhats_cond, labels=None, sample_weight=None, normalize=None)
  disp = ConfusionMatrixDisplay(confusion_matrix=cm_cond)
  fig, ax = plt.subplots(figsize=(6,6))
  disp.plot(ax=ax)
  plt.title(cond)
  plt.xticks((0,1),('0_back', '2_back'))
  plt.yticks((0,1),('0_back', '2_back'))
  plt.show()

  cr_body = classification_report(y_test[X_cond], yhats_cond, labels=None, target_names=['class 0', 'class 1'], sample_weight=None, digits=2, output_dict=False, zero_division='warn')
  print(cr_body)
  print()

"""#Cross validation"""

n_cv=8

cv = cross_val_score(model, X_test, y_test , cv=n_cv, scoring='recall_macro')
print(cv)

#visualize cv
f, ax = plt.subplots(figsize=(5, 3))
ax.boxplot(cv, vert=False, widths=.7)
ax.scatter(cv, np.ones(n_cv))
ax.set(
  xlabel="Accuracy",
  yticks=[],
  title=f"Average test accuracy: {cv.mean():.2%}"
)
ax.spines["left"].set_visible(False)
plt.show()