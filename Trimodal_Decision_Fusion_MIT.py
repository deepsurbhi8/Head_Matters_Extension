# -*- coding: utf-8 -*-
"""Decision_fusion_Regression_chunk_level_au_kin_audio_with_function_with_3new_weights.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1yf6qbxNovtftT5oiyA4-XREhcFR_6t4f
"""

import numpy as np
import pandas as pd
import glob
from sklearn.model_selection import train_test_split
from sklearn import linear_model
from math import sqrt
import matplotlib.pyplot as plt
from sklearn.model_selection import RepeatedKFold
from sklearn.metrics import mean_absolute_error
from sklearn import metrics
from sklearn.svm import SVR
from sklearn.decomposition import PCA
from keras.callbacks import ModelCheckpoint, Callback, EarlyStopping
import scipy.io as sio
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import regularizers
from tensorflow.keras.utils import to_categorical
from keras.layers import merge
# from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score
from sklearn import preprocessing
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout
from keras.models import Model
from keras.layers import Input, Dense, concatenate
# from sklearn.linear_model import Ridge

from google.colab import drive
drive.mount('/content/drive')

# onehot encoding of kineme sequence
def onehot_encoding(ks, nKineme):
    #print(ks)
    onehot_encoded = list()
    for k in ks:
        #print(k)
        vec = [0 for _ in range(nKineme)]
        vec[k-1] = 1
        onehot_encoded.append(vec)
        #print("Vector")
        #print(vec)
    return onehot_encoded


def ks_encoding(ks, nKineme):
    # ks is a numpy ndarray
    m, n = ks.shape #m=92, n=29
    #print(m, n)
    ks = ks.tolist() #converted to list
    encoded_features = np.asarray(
        [np.asarray(onehot_encoding(ks[i], nKineme)) for i in range(m)]
    )
    return encoded_features

# parameters
nKineme, seqLen, nClass = 16, 59, 1

def model_formation(chunk_size):
  seqLen = chunk_size-1
  callback = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=3)
  Model_kineme = Sequential()
  Model_kineme.add(LSTM(20,activation="tanh",dropout=0.2,recurrent_dropout=0.0,input_shape=(seqLen, 16)))
  Model_kineme.add(Dense(units = nClass, activation='linear'))
  opt = keras.optimizers.Adam(learning_rate=0.01)
  Model_kineme.compile(optimizer = opt, loss = 'mean_absolute_error')
  Model_kineme.summary()

  Model_AU = Sequential()
  Model_AU.add(LSTM(20,activation="tanh",dropout=0.2,recurrent_dropout=0.0,input_shape=(seqLen, 17)))
  Model_AU.add(Dense(units = nClass, activation='linear'))
  opt = keras.optimizers.Adam(learning_rate=0.01)
  Model_AU.compile(optimizer = opt, loss = 'mean_absolute_error')
  Model_AU.summary()

  Model_audio = Sequential()
  Model_audio.add(LSTM(20,activation="tanh",dropout=0.2,recurrent_dropout=0.0,input_shape=(seqLen, 23)))
  Model_audio.add(Dense(units = nClass, activation='linear'))
  opt = keras.optimizers.Adam(learning_rate=0.01)
  Model_audio.compile(optimizer = opt, loss = 'mean_absolute_error')
  Model_audio.summary()
  return Model_kineme, Model_AU, Model_audio, callback

def model_call(final_mat, audio_mat,y_data,chunk_size,label, Model_kineme, Model_AU, Model_audio, callback,x,y,z):
  seqLen = chunk_size-1
  #Lists to contain MAE and PCC
  train_mae =[]
  test_mae =[]
  train_PCC =[]
  test_PCC =[]
  n=1
  random_state = 42
  rkf = RepeatedKFold(n_splits=10, n_repeats=5, random_state=random_state)      #repeat kfold function
  for train_idx, test_idx in rkf.split(final_mat):
      train_features, test_features, train_labels, test_labels = final_mat[train_idx], final_mat[test_idx], y_data[train_idx], y_data[test_idx] 
      train_audio, test_audio = audio_mat[train_idx], audio_mat[test_idx]
      # print(train_features.shape, test_features.shape, train_labels.shape, test_labels.shape, train_audio.shape, test_audio.shape)
      train_kinemes = ks_encoding(train_features[:,0:seqLen], 16) #One hot encoding for kineme
      test_kinemes = ks_encoding(test_features[:,0:seqLen], 16)
      # print(train_features.shape)
      train_action = train_features[:, seqLen:] #Reshaping of data for AU
      test_action = test_features[:, seqLen:]
      train_aus = train_action.reshape((train_action.shape[0], seqLen, 17))
      test_aus = test_action.reshape((test_action.shape[0], seqLen, 17))

      train_audio_data = train_audio.reshape(train_audio.shape[0],seqLen,23) #reshaping of audio data
      test_audio_data = test_audio.reshape(test_audio.shape[0],seqLen,23) 
      # print(np.shape(train_kinemes), np.shape(test_kinemes), np.shape(train_aus), np.shape(test_aus), np.shape(train_audio_data), np.shape(test_audio_data))
     
      kineme_history = Model_kineme.fit(train_kinemes, train_labels, epochs = 30, batch_size = 32, validation_split=0.1,callbacks=[callback])  #Fitting the model 
      print("Kineme Model Training is Done")
      AU_history = Model_AU.fit(train_aus, train_labels, epochs = 30, batch_size = 32, validation_split=0.1,callbacks=[callback])
      print("AU Model Training is Done")
      audio_history = Model_audio.fit(train_audio_data, train_labels, epochs = 30, batch_size = 32, validation_split=0.1, callbacks=[callback])
      print("Audio model training is done")
     
      train_pred_kineme = Model_kineme.predict(train_kinemes)
      train_pred_au = Model_AU.predict(train_aus)
      train_pred_audio = Model_audio.predict(train_audio_data)  

      final_train_pred = x*train_pred_kineme + y*train_pred_au + z*train_pred_audio #change this -- whether we need two weighing parameters or three?   
      # kineme_history = final_model.fit([train_kinemes, train_aus,train_audio_data], train_labels, epochs = 30, batch_size = 32, validation_split = 0.1,callbacks=[callback])  
      # trainpredmerge=final_model.predict([train_kinemes, train_aus,train_audio_data])
      # y_pred_train = final_model.predict([train_kinemes, train_aus,train_audio_data])
      y_pred_train = np.around(final_train_pred,3)
      # print(y_pred_train.shape, train_labels.shape)
      
      test_pred_kineme = Model_kineme.predict(test_kinemes)
      test_pred_au = Model_AU.predict(test_aus)
      test_pred_audio = Model_audio.predict(test_audio_data)
      
      final_test_pred = x*test_pred_kineme + y*test_pred_au + z*test_pred_audio
      # y_pred_test = final_model.predict([test_kinemes, test_aus,test_audio_data])
      y_pred_test = np.around(final_test_pred,3)

      # print(y_pred_test.shape, test_labels.shape)
      train_mae.append(1-mean_absolute_error(train_labels, y_pred_train)) ##mean squarred train error
      # print(train_mae)
      test_mae.append(1-mean_absolute_error(test_labels, y_pred_test)) #mean squarred test error
      # print(test_mae)
      y_train = train_labels.reshape(-1,1)
      b = np.corrcoef(y_train.T,y_pred_train.T)
      train_PCC.append(b[0][1])
      y1 = test_labels.reshape(-1,1)
      a = np.corrcoef(y1.T,y_pred_test.T)
      test_PCC.append(a[0][1])
      print(n)
      n = n+1
  print("For label {0} and chunk_time {1}".format(label,chunk_time))
  print("Train-accuracy Test-accuracy Train-PCC Test-PCC")
  print("{0}±{1} {2}±{3} {4}±{5} {6}±{7}".format(round(np.array(train_mae).mean(),3),round(np.array(train_mae).std(),2), round(np.array(test_mae).mean(),3),round(np.array(test_mae).std(),2),round(np.array(train_PCC).mean(),3),round(np.array(train_PCC).std(),2),round(np.array(test_PCC).mean(),3),round(np.array(test_PCC).std(),2)))
  return train_mae, test_mae, train_PCC, test_PCC

label = 'RecommendHiring'

chunk_size = 60
chunk_time = chunk_size
#Data Formation
# /content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Audio_chunk_60.npy
kin_au_path = '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Kin_AU_chunk_' + str(chunk_time) + '.npy'
audio_path =  '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Audio_chunk_' + str(chunk_time) + '.npy'
label_path = '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Label_' + str(chunk_time) + '_' + label + '.npy'
final_mat = np.load(kin_au_path)
audio_mat_arr = np.load(audio_path)
y_data = np.load(label_path)
scaler = preprocessing.StandardScaler().fit(audio_mat_arr)
X_scaled = scaler.transform(audio_mat_arr)
audio_mat= X_scaled

# x = [0.33,1,0,0,0.25,0.5,0.25]
# y = [0.33,0,1,0,0.5,0.25,0.25]
# z = [0.33,0,0,1,0.25,0.25,0.5]

x = [0,0.5,0.5]
y = [0.5,0,0.5]
z = [0.5,0.5,0]
tr_acc = []
tr_std =[]
te_acc = []
te_std =[]
tr_pcc = []
pcc_std_tr = []
te_pcc = []
pcc_std_te =[]
for i in range(0,3):
  print(x[i],y[i],z[i])
  Model_kineme, Model_AU, Model_audio, callback = model_formation(chunk_size)
  train_mae, test_mae, train_PCC, test_PCC = model_call(final_mat, audio_mat,y_data,chunk_size,label, Model_kineme, Model_AU, Model_audio, callback,x[i],y[i],z[i])
  tr_acc.append(round(np.array(train_mae).mean(),3))
  tr_std.append(round(np.array(train_mae).std(),2))
  te_acc.append(round(np.array(test_mae).mean(),3))
  te_std.append(round(np.array(test_mae).std(),3))
  tr_pcc.append(round(np.array(train_PCC).mean(),3))
  pcc_std_tr.append(round(np.array(train_PCC).std(),2))
  te_pcc.append(round(np.array(test_PCC).mean(),3))
  pcc_std_te.append(round(np.array(test_PCC).std(),2))

Final_mat = np.vstack((np.asarray(x),np.asarray(y), np.asarray(z), np.asarray(tr_acc), np.asarray(tr_std),
                       np.asarray(te_acc),np.asarray(te_std), np.asarray(tr_pcc), np.asarray(pcc_std_tr), np.asarray(te_pcc), np.asarray(pcc_std_te)))
Final_mat = Final_mat.T

path = '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Weight_new3_' + str(chunk_size)+ label + '.csv'
pd.DataFrame(Final_mat).to_csv(path)

chunk_size = 30
chunk_time = chunk_size
#Data Formation
# /content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Audio_chunk_60.npy
kin_au_path = '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Kin_AU_chunk_' + str(chunk_time) + '.npy'
audio_path =  '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Audio_chunk_' + str(chunk_time) + '.npy'
label_path = '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Label_' + str(chunk_time) + '_' + label + '.npy'
final_mat = np.load(kin_au_path)
audio_mat_arr = np.load(audio_path)
y_data = np.load(label_path)
scaler = preprocessing.StandardScaler().fit(audio_mat_arr)
X_scaled = scaler.transform(audio_mat_arr)
audio_mat= X_scaled

# x = [0.33,1,0,0,0.25,0.5,0.25]
# y = [0.33,0,1,0,0.5,0.25,0.25]
# z = [0.33,0,0,1,0.25,0.25,0.5]

x = [0,0.5,0.5]
y = [0.5,0,0.5]
z = [0.5,0.5,0]
tr_acc = []
tr_std =[]
te_acc = []
te_std =[]
tr_pcc = []
pcc_std_tr = []
te_pcc = []
pcc_std_te =[]
for i in range(0,3):
  print(x[i],y[i],z[i])
  Model_kineme, Model_AU, Model_audio, callback = model_formation(chunk_size)
  train_mae, test_mae, train_PCC, test_PCC = model_call(final_mat, audio_mat,y_data,chunk_size,label, Model_kineme, Model_AU, Model_audio, callback,x[i],y[i],z[i])
  tr_acc.append(round(np.array(train_mae).mean(),3))
  tr_std.append(round(np.array(train_mae).std(),2))
  te_acc.append(round(np.array(test_mae).mean(),3))
  te_std.append(round(np.array(test_mae).std(),3))
  tr_pcc.append(round(np.array(train_PCC).mean(),3))
  pcc_std_tr.append(round(np.array(train_PCC).std(),2))
  te_pcc.append(round(np.array(test_PCC).mean(),3))
  pcc_std_te.append(round(np.array(test_PCC).std(),2))

Final_mat = np.vstack((np.asarray(x),np.asarray(y), np.asarray(z), np.asarray(tr_acc), np.asarray(tr_std),
                       np.asarray(te_acc),np.asarray(te_std), np.asarray(tr_pcc), np.asarray(pcc_std_tr), np.asarray(te_pcc), np.asarray(pcc_std_te)))
Final_mat = Final_mat.T

path = '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Weight_new3_' + str(chunk_size)+ label + '.csv'
pd.DataFrame(Final_mat).to_csv(path)

chunk_size = 15
chunk_time = chunk_size
#Data Formation
# /content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Audio_chunk_60.npy
kin_au_path = '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Kin_AU_chunk_' + str(chunk_time) + '.npy'
audio_path =  '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Audio_chunk_' + str(chunk_time) + '.npy'
label_path = '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Label_' + str(chunk_time) + '_' + label + '.npy'
final_mat = np.load(kin_au_path)
audio_mat_arr = np.load(audio_path)
y_data = np.load(label_path)
scaler = preprocessing.StandardScaler().fit(audio_mat_arr)
X_scaled = scaler.transform(audio_mat_arr)
audio_mat= X_scaled

# x = [0.33,1,0,0,0.25,0.5,0.25]
# y = [0.33,0,1,0,0.5,0.25,0.25]
# z = [0.33,0,0,1,0.25,0.25,0.5]

x = [0,0.5,0.5]
y = [0.5,0,0.5]
z = [0.5,0.5,0]
tr_acc = []
tr_std =[]
te_acc = []
te_std =[]
tr_pcc = []
pcc_std_tr = []
te_pcc = []
pcc_std_te =[]
for i in range(0,3):
  print(x[i],y[i],z[i])
  Model_kineme, Model_AU, Model_audio, callback = model_formation(chunk_size)
  train_mae, test_mae, train_PCC, test_PCC = model_call(final_mat, audio_mat,y_data,chunk_size,label, Model_kineme, Model_AU, Model_audio, callback,x[i],y[i],z[i])
  tr_acc.append(round(np.array(train_mae).mean(),3))
  tr_std.append(round(np.array(train_mae).std(),2))
  te_acc.append(round(np.array(test_mae).mean(),3))
  te_std.append(round(np.array(test_mae).std(),3))
  tr_pcc.append(round(np.array(train_PCC).mean(),3))
  pcc_std_tr.append(round(np.array(train_PCC).std(),2))
  te_pcc.append(round(np.array(test_PCC).mean(),3))
  pcc_std_te.append(round(np.array(test_PCC).std(),2))

Final_mat = np.vstack((np.asarray(x),np.asarray(y), np.asarray(z), np.asarray(tr_acc), np.asarray(tr_std),
                       np.asarray(te_acc),np.asarray(te_std), np.asarray(tr_pcc), np.asarray(pcc_std_tr), np.asarray(te_pcc), np.asarray(pcc_std_te)))
Final_mat = Final_mat.T

path = '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Weight_new3_' + str(chunk_size)+ label + '.csv'
pd.DataFrame(Final_mat).to_csv(path)

chunk_size = 10
chunk_time = chunk_size
#Data Formation
# /content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Audio_chunk_60.npy
kin_au_path = '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Kin_AU_chunk_' + str(chunk_time) + '.npy'
audio_path =  '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Audio_chunk_' + str(chunk_time) + '.npy'
label_path = '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Label_' + str(chunk_time) + '_' + label + '.npy'
final_mat = np.load(kin_au_path)
audio_mat_arr = np.load(audio_path)
y_data = np.load(label_path)
scaler = preprocessing.StandardScaler().fit(audio_mat_arr)
X_scaled = scaler.transform(audio_mat_arr)
audio_mat= X_scaled

# x = [0.33,1,0,0,0.25,0.5,0.25]
# y = [0.33,0,1,0,0.5,0.25,0.25]
# z = [0.33,0,0,1,0.25,0.25,0.5]

x = [0,0.25,0.5,0.25]
y = [0,0.5,0.25,0.25]
z = [1,0.25,0.25,0.5]
# x = [0,0.5,0.5]
# y = [0.5,0,0.5]
# z = [0.5,0.5,0]
tr_acc = []
tr_std =[]
te_acc = []
te_std =[]
tr_pcc = []
pcc_std_tr = []
te_pcc = []
pcc_std_te =[]
for i in range(0,4):
  print(x[i],y[i],z[i])
  Model_kineme, Model_AU, Model_audio, callback = model_formation(chunk_size)
  train_mae, test_mae, train_PCC, test_PCC = model_call(final_mat, audio_mat,y_data,chunk_size,label, Model_kineme, Model_AU, Model_audio, callback,x[i],y[i],z[i])
  tr_acc.append(round(np.array(train_mae).mean(),3))
  tr_std.append(round(np.array(train_mae).std(),2))
  te_acc.append(round(np.array(test_mae).mean(),3))
  te_std.append(round(np.array(test_mae).std(),3))
  tr_pcc.append(round(np.array(train_PCC).mean(),3))
  pcc_std_tr.append(round(np.array(train_PCC).std(),2))
  te_pcc.append(round(np.array(test_PCC).mean(),3))
  pcc_std_te.append(round(np.array(test_PCC).std(),2))

Final_mat = np.vstack((np.asarray(x),np.asarray(y), np.asarray(z), np.asarray(tr_acc), np.asarray(tr_std),
                       np.asarray(te_acc),np.asarray(te_std), np.asarray(tr_pcc), np.asarray(pcc_std_tr), np.asarray(te_pcc), np.asarray(pcc_std_te)))
Final_mat = Final_mat.T

path = '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Weight_remaining4_' + str(chunk_size)+ label + '.csv'
pd.DataFrame(Final_mat).to_csv(path)

x

label = "Friendly"
chunk_size = 10
chunk_time = chunk_size
#Data Formation
# /content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Audio_chunk_60.npy
kin_au_path = '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Kin_AU_chunk_' + str(chunk_time) + '.npy'
audio_path =  '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Audio_chunk_' + str(chunk_time) + '.npy'
label_path = '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Label_' + str(chunk_time) + '_' + label + '.npy'
final_mat = np.load(kin_au_path)
audio_mat_arr = np.load(audio_path)
y_data = np.load(label_path)
scaler = preprocessing.StandardScaler().fit(audio_mat_arr)
X_scaled = scaler.transform(audio_mat_arr)
audio_mat= X_scaled

x = [0.33,1,0,0,0.25,0.5,0.25]
y = [0.33,0,1,0,0.5,0.25,0.25]
z = [0.33,0,0,1,0.25,0.25,0.5]

# x = [0,0.5,0.5]
# y = [0.5,0,0.5]
# z = [0.5,0.5,0]
tr_acc = []
tr_std =[]
te_acc = []
te_std =[]
tr_pcc = []
pcc_std_tr = []
te_pcc = []
pcc_std_te =[]
for i in range(0,7):
  print(x[i],y[i],z[i])
  Model_kineme, Model_AU, Model_audio, callback = model_formation(chunk_size)
  train_mae, test_mae, train_PCC, test_PCC = model_call(final_mat, audio_mat,y_data,chunk_size,label, Model_kineme, Model_AU, Model_audio, callback,x[i],y[i],z[i])
  tr_acc.append(round(np.array(train_mae).mean(),3))
  tr_std.append(round(np.array(train_mae).std(),2))
  te_acc.append(round(np.array(test_mae).mean(),3))
  te_std.append(round(np.array(test_mae).std(),3))
  tr_pcc.append(round(np.array(train_PCC).mean(),3))
  pcc_std_tr.append(round(np.array(train_PCC).std(),2))
  te_pcc.append(round(np.array(test_PCC).mean(),3))
  pcc_std_te.append(round(np.array(test_PCC).std(),2))

Final_mat = np.vstack((np.asarray(x),np.asarray(y), np.asarray(z), np.asarray(tr_acc), np.asarray(tr_std),
                       np.asarray(te_acc),np.asarray(te_std), np.asarray(tr_pcc), np.asarray(pcc_std_tr), np.asarray(te_pcc), np.asarray(pcc_std_te)))
Final_mat = Final_mat.T

path = '/content/drive/MyDrive/Data_Labels_and_Code_for_chunk_level_analysis_kin_au_audio/Weight_' + str(chunk_size)+ label + '.csv'
pd.DataFrame(Final_mat).to_csv(path)

