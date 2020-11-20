# Federated learning workflow example using Triggerflow


In [this](example_federated_learning.ipynb) example, we have leveraged the flexibility of Triggerflow to implement a federated learning workflow using triggers. We use Triggerflow's triggers as a mechanism to accumulate and aggregate partial updates of the model from each client. The system is designed as a cyclic process where training rounds take place and a final aggregation phase updates the model and restarts the cycle.

## Explanation

<p align="center">
  <img width="65%" src="triggerflow-fedlearn-diagram.svg"></img>
</p>

At first, clients attempt to train asynchronously whenever they find an appropriate moment, and they do so by accessing a remote shared state guarded by synchronization lock of the same type. The shared state contains the model information for that round, that is, the storage key to the current model weights, the task that is desired to be performed, the value of the interval of time representing how long the task is expected to take, and a table of timestamps.

### Start
A client tries to take a place and contribute in a round by putting their timestamp into a free spot of the round table. If it cannot find a spot, then it checks if one of the timestamps is older than the permitted interval, and in case it is it takes that spot. The client proceeds to locally train the model and upon end it checks the model state again. If its timestamp is still in the place it acquired from the table, which should always be the case when the duration of the training is within the interval, then it marks that place in the table, saves the trained model weights to a random unique key into the cloud storage and finally sends an event to the first trigger containing that resulting key. 

### Aggregation trigger
The first trigger operates with a custom condition. The condition acts as a simple join but it also accumulates client results until it fires. When it activates, the trigger fires the action which is to invoke an IBM Cloud Function, called the aggregator. The aggregator receives the client results keys and its job is to perform a model update by aggregating the results of that round. After aggregating the trained deltas of all clients or the score obtained from testing on each clients data (in case it was a round of testing), the aggregator stores the result on the cloud and deletes all the intermediate data stored in it. At last, it generates a completion event that is sent to the second trigger.

### Round restart trigger
The second trigger is responsible for starting a new round by resetting the shared model state. Actually, when the last client completes the task, it marks its place in the table and finds that all tasks have been completed. It is then when the lock it had acquired to access the shared state is not released, intentionally blocking the round. Therefore, when the second trigger receives the event from the aggregator, it performs a custom action that not only updates the state by clearing the round table, but it also releases the lock allowing clients to start contributing again. This second trigger can also receive an other type of event with the purpose to change the task of the next round.

<br/><br/>
In contrast to the majority of currently proposed systems, which are based on a centralized master component responsible of synchronizing all clients, this approach enables time decoupling and guarantees high scalability by design, as well as fault tolerance with event sourcing. This solution also ensures code transparency and simplicity, since code is written entirely in Python and only internally we make use of specialized triggers.