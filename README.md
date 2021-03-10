# Masters Thesis Code Execution Manual

 - Set up the virtual conda environment by running the following command:
    
     ```sh
        $ conda create -f requirements.yml
     ```


 - The dataset folder should be organized as follows:

>  datasets  
├── img
├── gt

 - Then run the following command to train the model:

     ```sh
        $ python train.py
     ```

 - Then run the evaluation script to evaluate the model:

     ```sh
        $ python eval.py
     ```



