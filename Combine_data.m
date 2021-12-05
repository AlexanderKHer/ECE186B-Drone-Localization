%%

data = [table2array(readtable('2NN_dataset_flight.1.csv'))
        table2array(readtable('2NN_dataset_flight.2.csv'))
        table2array(readtable('2NN_dataset_flight.3.csv'))
        table2array(readtable('2NN_dataset_flight.4.csv'))
        table2array(readtable('2NN_dataset_flight.5.csv'))
        table2array(readtable('2NN_dataset_flight.6.csv'))
        table2array(readtable('2NN_dataset_flight.7.csv'))
        table2array(readtable('2NN_dataset_flight.8.csv'))];
    
writematrix(data,'2NN_all_dataset.csv')
