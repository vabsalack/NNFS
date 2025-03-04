import numpy as np
from typing import List, Dict, Optional, Tuple, Callable, TypeVar, Union, Any
from numpy.typing import NDArray, DTypeLike, ArrayLike

Float64Array2D = np.ndarray[Tuple[int, int], np.dtype[np.float64]]

class Layer_Input:
    """
    Layer_Input class represents the input layer of the neural network.
    """

    def forward(self, inputs: ArrayLike) -> None: 
        """
        Performs a forward pass of the input layer.

        #### Parameters:
        inputs (NDArray): Input data.
        """
        self.output = np.array(inputs, dtype=np.float64)


class Layer_Dense:
    """
    #### what 
        - create Dense Layer 
        - args: nintputs, nneurons, wL1, wL2, bL1, bL2
    #### Improve
        - experiment with other initialization method such as he, xavier, etc.
    #### Flow
        - [init -> (forward -> backward)]
    """

    def __init__(self, n_inputs: int, 
                 n_neurons: int,
                 weight_regularizer_L1: Union[float, int] = 0,
                 weight_regularizer_L2: Union[float, int] = 0, 
                 bias_regularizer_L1: Union[float, int] = 0,
                 bias_regularizer_L2: Union[float, int] = 0) -> None:
        """
        #### Note
            - weights initialization is one of crucial part in model convergence.
        """
        self.weights = 0.01 * np.random.randn(n_inputs, n_neurons) 
        self.biases = np.zeros((1, n_neurons))
        # L1 strength
        self.weight_regularizer_L1 = weight_regularizer_L1
        self.bias_regularizer_L1 = bias_regularizer_L1
        # L2 strength
        self.weight_regularizer_L2 = weight_regularizer_L2
        self.bias_regularizer_L2 = bias_regularizer_L2

    def forward(self, inputs: Float64Array2D) -> None:
        self.inputs = inputs
        self.output = np.dot(inputs, self.weights) + self.biases
        
    def backward(self, dvalues: Float64Array2D) -> None:
        """
        #### Note
        - compute gradients.
        - apply regularization to computed gradients.
        """
        self.dweights = np.dot(self.inputs.T, dvalues)
        self.dbiases = np.sum(dvalues, axis=0, keepdims=True)
        self.dinputs = np.dot(dvalues, self.weights.T)
        # apply L1
        if self.weight_regularizer_L1 > 0:
            dL1 = np.ones_like(self.weights)
            dL1[self.weights < 0] = -1
            self.dweights += self.weight_regularizer_L1 * dL1
        if self.bias_regularizer_L1 > 0:
            dL1 = np.ones_like(self.biases)
            dL1[self.biases < 0] = -1
            self.dbiases += self.bias_regularizer_L1 * dL1
        # apply L2
        if self.weight_regularizer_L2 > 0:
            self.dweights += 2 * self.weight_regularizer_L2 * self.weights
        if self.bias_regularizer_L2 > 0:
            self.dbiases += 2 * self.bias_regularizer_L2 * self.biases

        
class Layer_Dropout:
    """
    #### what
        - Dropout is a regularization technique where randomly selected neurons are ignored during training.
        - args: rate (percentage of neurons to be deactivated)
    #### Improve
    #### Flow
        - [init -> (forward -> backward)]
        - create binary mask from sample
    """

    def __init__(self, rate: Union[float, int]) -> None:
        """
        - rate = 1-rate # np.random.binomial expects probability of success (1) not failure (0)
        """
        self.rate = 1 - rate

    def forward(self, 
                inputs: Float64Array2D, 
                training: bool) -> None:
        """
        - divide the mask by the rate to scale the values.
        """
        self.inputs = inputs
        if not training:
            self.output = inputs.copy()
            return
        self.binary_mask = np.random.binomial(1, self.rate, size=self.inputs.shape) / self.rate
        self.output = self.inputs * self.binary_mask

    def backward(self, dvalues: Float64Array2D) -> None:
        self.dinputs = dvalues * self.binary_mask


class Activation_ReLU:
    """
    #### what
        - introduce non-linearity in the network.
    #### Improve
        - leaky ReLu, Parametric ReLu, Exponential ReLu, etc.
    #### Flow
        - [(forward -> backward), predictions]
        - ReLu(x) = max(0, x)
    """

    def forward(self, 
                inputs: Float64Array2D, 
                training: bool) -> None:
        self.inputs = inputs
        self.output = np.maximum(0, inputs)

    def backward(self, dvalues: Float64Array2D) -> None:
        self.dinputs = dvalues.copy()
        self.dinputs[self.inputs <= 0] = 0

    def predictions(self, outputs: Float64Array2D) -> Float64Array2D:
        return outputs


class Activation_Softmax:
    """
    #### what
        - convert raw scores into probabilities. 
        - use in the output layer of a neural network for **multi-class** classification.
    #### Improve
    ### Flow
        - [(forward -> backward), predictions]
        - softmax(x) = exp(x) / sum(exp(x))
        - pair it with compatible loss function such as categorical cross-entropy loss.
    """

    def forward(self, 
                inputs: Float64Array2D, 
                training: bool) -> None:
        self.inputs = inputs
        exp_values = np.exp(inputs - np.max(inputs, axis=1, keepdims=True))
        probabilities = exp_values / np.sum(exp_values, axis=1, keepdims=True)
        self.output = probabilities

    def backward(self, dvalues: Float64Array2D) -> None:
        """
        #### How
            - softmax derivative is calculated using jacobian matrix (square matrix)
        """
        self.dinputs = np.empty_like(dvalues)
        for index, (single_output, single_dvalues) in enumerate(zip(self.output, dvalues)):
            single_output = single_output.reshape(-1, 1)
            jacobian_matrix = np.diagflat(single_output) - np.dot(single_output, single_output.T)
            self.dinputs[index] = np.dot(jacobian_matrix, single_dvalues)

    def predictions(self, outputs: Float64Array2D) -> np.ndarray[Tuple[int], np.dtype[np.int64]]:
        return np.argmax(outputs, axis=1)


class Activation_Sigmoid:
    """
    #### What
        - use primarily in the multi-label classification problem. Each output neurons represents seperate class on its own.
        - use in the output layer of a neural network for binary logistic regression models
    #### Improve
        - Accuracy
            - Use subset accuracy when exact matches are critical.
            - For tasks where partial matches are acceptable(default here), consider using Hamming Loss, F1 Score, or Jaccard Similarity.
    ### Flow
        - [(forward -> backward), predictions]
        - sigmoid(x) = 1 / (1 + exp(-x))
        - pair it with compatible loss function such as binary cross-entropy loss.
    """

    def forward(self, 
                inputs: Float64Array2D, 
                training: bool) -> None:
        self.inputs = inputs
        self.output = 1 / (1 + np.exp(-inputs))

    def backward(self, dvalues: Float64Array2D) -> None:
        """
        - derivate: sigmoid'(x) = sigmoid(x) * (1 - sigmoid(x))
        """
        self.dinputs = dvalues * (1 - self.output) * self.output

    def predictions(self, outputs: Float64Array2D) -> np.ndarray[Tuple[int, int], np.dtype[np.int64]]:
        """
            - product of arr: NDArray[bool_] and x: int is y: NDArray[int64]
            - array([False, True]) * -2 = array([0, -2])
        """
        return (outputs > 0.5) * 1


class Activation_Linear:
    """
    #### what
        - Linear activation function is used to pass the input directly to the output without any modification.
        - use in the output layer for regression tasks where we need to predict continuous values.
    #### Improve
    ### Flow
        - [(forward -> backward), predictions]
        - f(x) = x
        - pair it with compatible loss function such as mean squared/absolute error loss.
    """

    def forward(self, 
                inputs: Float64Array2D, 
                training: bool) -> None:
        self.inputs = inputs
        self.output = inputs

    def backward(self, dvalues: Float64Array2D) -> None:
        self.dinputs = dvalues.copy()

    def predictions(self, outputs: Float64Array2D) -> Float64Array2D:
        return outputs

class Loss:
    """
    #### what
        - Base class for loss functions.
    #### Improve
        - Implement additional loss functions as needed.
    ### Flow
        - [remember_trainable_layers -> regularization_loss -> calculate]
        - remember_trainable_layers method sets self.trainable_layers property.
        - regularization_loss method calculates the regularization loss using layers in self.trainable_layers.
        - calculate method calculates the data loss using child class's forward method and regularization loss from regularization_loss method.
    """

    def remember_trainable_layers(self, trainable_layers: List[Union[Layer_Dense]]) -> None:
        self.trainable_layers = trainable_layers

    def regularization_loss(self) -> float:
        regularization_loss: float = .0
        for layer in self.trainable_layers:
            # L1 penalty
            if layer.weight_regularizer_L1 > 0:
                regularization_loss += layer.weight_regularizer_L1 * np.sum(np.abs(layer.weights))
            if layer.bias_regularizer_L1 > 0:
                regularization_loss += layer.bias_regularizer_L1 * np.sum(np.abs(layer.biases))
            # L2 penalty
            if layer.weight_regularizer_L2 > 0:
                regularization_loss += layer.weight_regularizer_L2 * np.sum(layer.weights * layer.weights)
            if layer.bias_regularizer_L2 > 0:
                regularization_loss += layer.bias_regularizer_L2 * np.sum(layer.biases * layer.biases)
        return regularization_loss

    def calculate(self, 
                  output: Float64Array2D, 
                  y, # y type can be one-hot encoded or sparse lables
                  *, 
                  include_regularization: bool=False) -> Union[float, Tuple[np.float64, np.float64]]:
        """
        #### Note
            - data loss is the mean of sample losses
            - regularization loss is the sum of L1 and L2 penalties
            - returns only data loss by default
        """
        sample_losses = self.forward(output, y)
        data_loss = np.mean(sample_losses)
        if not include_regularization:
            return data_loss
        return data_loss, self.regularization_loss()
    

class Loss_CategoricalCrossentropy(Loss):
    """
   #### what
        - Categorical cross-entropy loss function is used in multi-class (3 and more) classification tasks.
        - It's the negative-log-likelihood of likelihood function 
        - use to find the MLE (Maximum Likelihood Estimation) of the model.
    #### Improve
    #### Flow
        - [forward -> backward]
        - formula: -sum(y_true * log(y_pred))
    """
    def forward(self,
                y_pred: Float64Array2D, 
                y_true) -> np.ndarray[Tuple[int], np.dtype[np.float64]]:  # y_true type can be one-hot encoded or sparse lables
        """
        #### Note
            - clips the predicted values to prevent division by zero, log of zero is undefined and derivate of log(x) is 1/x precision overflows.
            - clips both sides to not drag mean towards any value
            - computes the negative log likelihood of only the correct class probabilities. -( 0.log(x.x) + 1.log(x.x) + 0.log(x.x) + 0.log(x.x) ) 
        """
        samples = len(y_pred)
        y_pred_clipped = np.clip(y_pred, 1e-7, 1 - 1e-7)
        if len(y_true.shape) == 1:
            correct_confidences = y_pred_clipped[range(samples), y_true]
        elif len(y_true.shape) == 2:
            correct_confidences = np.sum(y_pred_clipped * y_true, axis=1)
        negative_log_likelihoods = -np.log(correct_confidences)
        return negative_log_likelihoods
        

    def backward(self, dvalues: Float64Array2D, 
                 y_true) -> None: 
        """
        #### Note
            - Expects y_true to be one-hot encoded.
            - **normalizes the gradient by the number of samples.**
        """
        samples = len(dvalues)
        labels = len(dvalues[0])
        if len(y_true.shape) == 1:
            y_true = np.eye(labels)[y_true]
        
        self.dinputs = -y_true / dvalues
        self.dinputs = self.dinputs / samples


class Activation_Softmax_Loss_CategoricalCrossentropy:
    """
    #### what
        - Softmax classifier is a combination of softmax activation and categorical cross-entropy loss.
        - peforms backward pass in a single step faster than traditional (softmax and categorical cross-entropy loss) backward methods.
        - gradients of loss functions with respect to the penultimate layer's outputs reduced to a single step.
    #### Improve    
    #### Flow
        - [init -> forward -> backward]
        - formula = predicted values - true values
    """

    def __init__(self) -> None:
        self.activation = Activation_Softmax()
        self.loss = Loss_CategoricalCrossentropy()

    def forward(self, inputs: Float64Array2D, y_true) -> np.float64:
        """
        #### Note
            - performs forward method of softmax and loss classes.
        """
        self.activation.forward(inputs)
        self.output = self.activation.output
        return self.loss.calculate(self.output, y_true)
    
    def backward(self, dvalues: Float64Array2D, y_true) -> None:
        """
        #### Note
            - expects y_true to be sparse labels
            - copy the dvalues to self.dinputs
            - compute gradient and normalize them
        """
        samples = len(dvalues)
        if len(y_true.shape) == 2:
            y_true = np.argmax(y_true, axis=1)
        self.dinputs = dvalues.copy()
        self.dinputs[range(samples), y_true] -= 1
        self.dinputs = self.dinputs / samples

class Loss_BinaryCrossentropy(Loss):
    """
    what it is?
        * Binary cross-entropy loss function is used in binary regression models.
        * used primarily in the multi-label classification problem.
    where we can improvize?
    why it is used?
        * Unlike categorical cross-entropy, it measures negative-log-likelihood of each output neurons seperately and average them.
    how it works?
        * forward
        * backward
        * formula: -sum(y_true * log(y_pred) + (1 - y_true) * log(1 - y_pred))
        * Each sample loss is a vector of output neuron's losses and it's average used as the final loss for that sample.
    """

    def forward(self, 
                y_pred: Float64Array2D, 
                y_true: np.ndarray[Tuple[int, int], np.dtype[np.int64]]) -> np.array[Tuple[int], np.dtype[np.float64]]:
        """
        what it does?
            * clips the predicted values to prevent division by zero, log of zero is undefined and derivate of log(x) is 1/x precision overflows.
            * clips both sides to not drag mean towards any value
            * calculates negative log likelihood of each outputs of a sample and average them.
        """
        # np.log(1e-323) = -inf
        y_pred_clipped = np.clip(y_pred, 1e-7, 1 - 1e-7)
        sample_losses = -(y_true * np.log(y_pred_clipped) + (1 -y_true) * np.log(1 - y_pred_clipped))
        sample_losses = np.mean(sample_losses, axis=-1)
        return sample_losses

    def backward(self, 
                 dvalues: Float64Array2D, 
                 y_true: np.ndarray[Tuple[int, int], np.dtype[np.int64]]) -> None:
        """
        what it does?
            * Final loss of a sample is average of each output neuron's loss.
            * gradient of sub each neuron's loss is - ((y_true / y_pred) - (1 - y_true) / (1 - y_pred))
            * partial derivative of final loss w.r.t output neuron's value is - ((y_true / y_pred) - (1 - y_true) / (1 - y_pred)) / outputs
            * normalize the gradient by the number of samples in the batch.
        """
        samples = len(dvalues)
        outputs = len(dvalues[0])
        clipped_dvalues = np.clip(dvalues, 1e-7, 1 - 1e-7)
        self.dinputs = -((y_true / clipped_dvalues) - (1 - y_true)/(1 - clipped_dvalues)) / outputs
        self.dinputs /= samples


class Loss_MeanSquaredError(Loss):
    """
    what it is?
        * Mean squared error(MSE) L2 loss function is used in single or multiple output regression tasks.
    where we can improvize?
    why it is used?
        * MSE(L2) most commonly used loss function for regression tasks over MAE(L1).
    how it works?
        * forward
        * backward
        * Assumption is that the error residuals are normally distributed.
        * refer to it's likelihood function for intuitive understanding.
    """

    def forward(self, y_pred: Float64Array2D,
                 y_true: Float64Array2D) -> np.array[Tuple[int], np.dtype[np.float64]]:
        """
        * loss formula: mean((y_true - y_pred)^2) applies to each sample in a batch.
        """
        sample_losses = np.mean((y_true - y_pred)**2, axis=-1)
        return sample_losses

    def backward(self, dvalues: Float64Array2D, 
                 y_true: Float64Array2D) -> None:
        """
        what it does?
            * computes gradient of loss functions with respect to the predicted values.
            * formula = -2 * (y_true - y_pred) / outputs is for one of predicted outputs in a sample.
            * normalize the gradient by the number of samples in the batch.
        """
        samples = len(dvalues)
        outputs = len(dvalues[0])
        self.dinputs = -2 * (y_true - dvalues) / outputs
        self.dinputs = self.dinputs / samples


class Loss_MeanAbsoluteError(Loss):
    """
    what it is?
        * Mean absolute error(MAE) L1 loss function is used in single or multiple output regression tasks.
    where we can improvize?
    why it is used?
        * MAE(L1) is less sensitive to outliers than MSE(L2).
        * It is used in regression tasks where outliers are present.
    how it works?
        * forward
        * backward
        * Assumption is that the error residuals are Laplace distributed.
    """

    def forward(self, 
                y_pred: Float64Array2D, 
                y_true: Float64Array2D) -> np.array[Tuple[int], np.dtype[np.float64]]:
        """
        * loss formula: mean(abs(y_true - y_pred)) applies to each sample in a batch.
        """
        sample_losses = np.mean(np.abs(y_true - y_pred), axis=-1)
        return sample_losses

    def backward(self, 
                 dvalues: Float64Array2D,
                y_true: Float64Array2D) -> None:
        """
        what it does?
            * computes gradient of loss functions with respect to the predicted values.
            * formula = sign(y_true - y_pred) / outputs is for one of predicted outputs in a sample.
            * The derivative of an absolute value equals 1 if this value is greater than 0, or -1 if it’s less than 0. The derivative does not exist for a value of 0
            * np.sign returns -1 for negative values, 0 for 0, and 1 for positive values.
            * normalize the gradient by the number of samples in the batch.
        """
        samples = len(dvalues)
        outputs = len(dvalues[0])
        self.dinputs = np.sign(y_true - dvalues) / outputs
        self.dinputs = self.dinputs / samples

class Optimizer_SGD:
    """
    what it is?
        * Stochastic Gradient Descent (SGD) is the simplest optimizer.
        * The SGD optimizer with momentum is usually one of 2 main choices for an optimizer in practice next to the Adam optimizer.
    where we can improvize?
        * calculate the limit of iterations before learning rate decays to near zero.
        * how about implementing a decayer for momentum?
    why it is used?
        * It comes with learning rate decay and GD with momentum. Both are crucial for faster convergence.
    how it works?
        * init
        * pre_update_params
        * update_params
        * post_update_params
        * Exponential decay, think about the 1/x graph values in range of x in [1, inf]. get the idea. lr = lr / (1 + x)
        * Implementation of momentum uses EMWA (Exponentially Weighted Moving Average) of gradients.
        * weight_update = Wn + Wn-1*M^(n-1) + Wn-2*M^(n-2) + ... + W1*M^0. updates involved of 100% of current gradient and exponential decays of past gradients.
    """
    def __init__(self, 
                 learning_rate: float = 1., 
                 decay: float = 0., 
                 momentum: float = 0.) -> None:
        self.learning_rate = learning_rate
        self.current_learning_rate = learning_rate
        self.decay = decay
        self.iterations = 0
        self.momentum = momentum

    def pre_update_params(self):
        if self.decay:
            self.current_learning_rate = self.learning_rate * (1. / (1. + self.decay * self.iterations))

    def update_params(self, Layer: Layer_Dense) -> None:
        if self.momentum:
            if not hasattr(Layer, "weight_momentums"):
                Layer.weight_momentums = np.zeros_like(Layer.weights)
                Layer.bias_momentums = np.zeros_like(Layer.biases)
            weight_updates = self.momentum * Layer.weight_momentums - self.current_learning_rate * Layer.dweights
            Layer.weight_momentums = weight_updates
            bias_updates = self.momentum * Layer.bias_momentums - self.current_learning_rate * Layer.dbiases
            Layer.bias_momentums = bias_updates
        else: # Vanilla SGD updates (as before momentum update)
            weight_updates = -self.current_learning_rate * Layer.dweights
            bias_updates = -self.current_learning_rate * Layer.dbiases
        Layer.weights += weight_updates
        Layer.biases += bias_updates

    def post_update_params(self) -> None:
        self.iterations += 1

class Optimizer_Adagrad:
    """
    what it is?
        * Adagrad optimizer is an adaptive learning rate optimizer.
    where we can improvize?
        * check how division of root squared of past gradients affects the learning rate. especially values le 0
        * In the very first steps, the learning rate is the update to the parameters Layer.weights += -self.current_learning_rate * 1
        * Initially, the learning rate is very high, and the updates are very large. lead to divergence.
        * learning does stall.
    why it is used?
        * The idea here is to normalize updates made to the features.
        * This optimizer is not widely used, except for some specific applications.
    how it works?
        * init, pre_update_params, update_params, post_update_params
        * formula: lr = lr / (sqrt(cache) + epsilon)
        * test it out in practice, notice how adaptation works in numbers.
        * After no of epochs, the epoch gradients always less than cache gradients. results in diminishing gradients.
    """
    def __init__(self, 
                 learning_rate: float = 1.,
                 decay: float = 0., 
                 epsilon: float = 1e-7) -> None:
        self.learning_rate = learning_rate
        self.current_learning_rate = learning_rate
        self.decay = decay
        self.iterations = 0
        self.epsilon = epsilon

    def pre_update_params(self) -> None:
        if self.decay:
            self.current_learning_rate = self.learning_rate * (1. / (1. + self.decay * self.iterations))

    def update_params(self, Layer: Layer_Dense) -> None:
        if not hasattr(Layer, "weight_cache"):
            Layer.weight_cache = np.zeros_like(Layer.weights)
            Layer.bias_cache = np.zeros_like(Layer.biases)
        Layer.weight_cache += Layer.dweights**2
        Layer.bias_cache += Layer.dbiases**2
        Layer.weights += -self.current_learning_rate * Layer.dweights / (np.sqrt(Layer.weight_cache) + self.epsilon)    
        Layer.biases += -self.current_learning_rate * Layer.dbiases / (np.sqrt(Layer.bias_cache) + self.epsilon)        

    def post_update_params(self) -> None:
        self.iterations += 1

class Optimizer_RMSprop:
    """
    what it is?
        * RMSprop optimizer is an adaptive learning rate optimizer.
        * It is a variant of Adagrad optimizer.
    where we can improvize?
    why it is used?
        * It has decaying caching mechanism, which prevents the learning rate from becoming too small.
        * learning does not stall.
    how it works?
        * init, pre_update_params, update_params, post_update_params
        * learning rate of 0.001 works well and it's default in popular frameworks.   
    """
    def __init__(self, 
                 learning_rate: float = 0.001, 
                 decay: float = 0., 
                 epsilon: float = 1e-7, 
                 beta: float = 0.9) -> None:
        self.learning_rate = learning_rate
        self.current_learning_rate = learning_rate
        self.decay = decay
        self.iterations = 0
        self.epsilon = epsilon
        self.beta = beta

    def pre_update_params(self) -> None:
        if self.decay:
            self.current_learning_rate = self.learning_rate * (1. / (1. + self.decay * self.iterations))

    def update_params(self, Layer: Layer_Dense) -> None:
        """
        what it does?
            * formula: cache = cache * beta + (1 - beta) * gradient^2. EMWA discounting past gradients.
            * (1 - beta) contribution term and (beta) decay term. test assigned each variable to it.
        """
        if not hasattr(Layer, "weight_cache"):
            Layer.weight_cache = np.zeros_like(Layer.weights)
            Layer.bias_cache = np.zeros_like(Layer.biases)
        Layer.weight_cache = self.beta * Layer.weight_cache + (1 - self.beta) * Layer.dweights**2
        Layer.bias_cache += self.beta * Layer.bias_cache + (1- self.beta) * Layer.dbiases**2
        Layer.weights += -self.current_learning_rate * Layer.dweights / (np.sqrt(Layer.weight_cache) + self.epsilon)        
        Layer.biases += -self.current_learning_rate * Layer.dbiases / (np.sqrt(Layer.bias_cache) + self.epsilon)        

    def post_update_params(self) -> None:
        self.iterations += 1

class Optimizer_Adam:
    """
    what it is?
        * Adaptive Moment Estimation optimizer is an adaptive learning rate optimizer.
        * It is a combination of RMSprop and Momentum optimizers.
    where we can improvize?
        * Adam requires additional memory to store the first and second moment estimates for each parameter.
    why it is used?
        * Combines the power of both firsand second moments
        * Commonly used in deep learning tasks.
        * It is robust to noisy gradients and sparse gradients
    how it works?
        * init, pre_update_params, update_params, post_update_params
        * bias correction, In inital stages, the first and second moments are biased towards zero.
    """
    def __init__(self, 
                 learning_rate: float = 0.001, 
                 decay: float = 0., 
                 epsilon: float = 1e-7, 
                 beta_1: float = 0.9, 
                 beta_2: float = 0.999) -> None:
        self.learning_rate = learning_rate
        self.current_learning_rate = learning_rate
        self.decay = decay
        self.iterations = 0
        self.epsilon = epsilon
        self.beta_1 = beta_1        
        self.beta_2 = beta_2     

    def pre_update_params(self) -> None:
        if self.decay:
            self.current_learning_rate = self.learning_rate * (1. / (1. + self.decay * self.iterations))

    def update_params(self, Layer: Layer_Dense) -> None:
        """
        what it does?
            * params update: w_t = w_t-1 - lr * m_t / (sqrt(v_t) + epsilon)
            * first moment:  m_t = beta_1 * m_t-1 + (1 - beta_1) * gradient
            * second moment: v_t = beta_2 * v_t-1 + (1 - beta_2) * gradient^2
        """
        if not hasattr(Layer, "weight_cache"):
            Layer.weight_momentums = np.zeros_like(Layer.weights)
            Layer.bias_momentums = np.zeros_like(Layer.biases)
            Layer.weight_cache = np.zeros_like(Layer.weights)
            Layer.bias_cache = np.zeros_like(Layer.biases)
        # first moment
        Layer.weight_momentums = self.beta_1 * Layer.weight_momentums + (1 - self.beta_1) * Layer.dweights
        Layer.bias_momentums = self.beta_1 * Layer.bias_momentums + (1 - self.beta_1) * Layer.dbiases
        weight_momentums_corrected = Layer.weight_momentums / (1 - self.beta_1 ** (self.iterations + 1)) # bias correction
        bias_momentums_corrected = Layer.bias_momentums / (1 - self.beta_1 ** (self.iterations + 1))
        # second moment
        Layer.weight_cache = self.beta_2 * Layer.weight_cache + (1 - self.beta_2) * Layer.dweights**2
        Layer.bias_cache = self.beta_2 * Layer.bias_cache + (1 - self.beta_2) * Layer.dbiases**2
        weight_cache_corrected = Layer.weight_cache / (1 - self.beta_2 ** (self.iterations + 1)) # bias correction
        bias_cache_corrected = Layer.bias_cache / (1 - self.beta_2 ** (self.iterations + 1))
        # params updates
        Layer.weights += -self.current_learning_rate * weight_momentums_corrected / (np.sqrt(weight_cache_corrected) + self.epsilon)
        Layer.biases += -self.current_learning_rate * bias_momentums_corrected / (np.sqrt(bias_cache_corrected) + self.epsilon)

    def post_update_params(self) -> None:
        self.iterations += 1





           


    

