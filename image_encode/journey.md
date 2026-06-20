test.py is using the all-MiniLM-L6-v2  sentence transfomer to encode 
test2.py is using all-mpnet-base-v2 this model for whatever the length of sentence it produces 768 dimension which is converted to 3 channels so 768 /3  = 256 RGB pixels which is arranged in 16 by 16 boxes , this is done to make autoencoder understand by textual information by treating semantic patterns as spatial strcutures.
