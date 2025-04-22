"""
Copyright 2024 JoS QUANTUM GmbH

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

"""
Class to perform principal component analysis. 
Recall that due to the nature 
of NISQ devices, we cannot just aim to maximise the variance 
but also need to reduce the data size so that it is 
compatible with these devices. 
The data needs to be convered to matrix format, i.e. X is a matrix.
"""
import numpy as np
from scipy.spatial.distance import pdist, squareform


class PCA_demo: # Assuming a (maximum) 20 qubit quantum computer, we have set num_components=5 as default.
    # Note that we are also assuming a simple encoding scheme where each individual parameter is 
    # mapped to one qubit. This may not be the case.
    
    # For images, need to use the grayscale (see preproc_utils) and flatten functions beforehand (see notebook)
    def __init__(self, num_components =20):
        #number of pca components
        self.num_components = num_components
        # vector with component weights 
        self.components = None
        self.mean = None
        #standard deviation
        self.std = None 
        #handling standard deviation = 0 
        self.std_filled = None 
        #how much variance is captured by the num_components
        self.variance_ratio = None 


    def fit(self, X): #X needs to be a matrix, i.e for images use imread etc
        """
        Find principal components and sort them in descending order
        """
        # data standardization; (X - mean)/std
        self.mean = np.mean(X, axis = 0)
        self.std = np.std(X, axis = 0)
         #handleing zero standard deviation
        self.std_filled = self.std.copy()
        self.std_filled[self.std == 0] = 1.0
        X = (X- self.mean)/self.std_filled
        # calculate eigenvalues & eigenvectors of the covariance matrix
        linear = np.cov(X.T)
        # for some reason, eig gives me complex numbers (complex = 0)
        eigenvalues, eigenvectors = np.linalg.eigh(linear)  
            
        # sort eigenvalues & eigenvectors in descending order
        sort_idx = np.argsort(eigenvalues)[::-1]
        eigenvalues   = eigenvalues[sort_idx]
        eigenvectors  = eigenvectors[:, sort_idx]
        
        # store principal components & variance captured by components
        self.components = eigenvectors[:,:self.num_components]
        self.variance_ratio = np.sum(eigenvalues[:self.num_components]) / np.sum(eigenvalues) 
        # This will allow you to see the cumulative variance ratio, i.e. the amount of variance each pca component adds to the total variance
        self.cumulative_variance_ratio = np.cumsum(self.variance_ratio) # added 22/05

    
    
    def transform(self, X): #X needs to be a matrix
        """
        Transform data with linear or radial PCA
        """
        # data standardization 
        X = (X- self.mean)/self.std_filled
        return np.dot(X, self.components.T)
            
        
    

    
