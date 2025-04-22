# Principal Component Analysis with a twist

**Functionality:**
We describe the desired functionality of the informed scanning and provide two example workflows.
* **Build the Sampler:**
    * Generate samples based on a specified probability distribution.
    * Focus sampling around the distribution's center or region of high probability.
* **Evaluate and adjust:**
    * Evaluate the generated samples, using the chosen/given loss function.
    * Use the evaluation results to adjust the parameters or shape of the underlying probability distribution. This is an iterative process.
* **Dimensionality Reduction and Subspace Analysis:**
    * Identify a 2D subspace.
    * Select the subspace that captures the highest variance in the **loss function** with respect to the input samples.
    * Perform a *Hyvis* scan within this 2D subspace.

**Example Workflow (Multivariate Gaussian):**

1.  **Initial Sampling:**
    * Sample data points from a multivariate Gaussian distribution.
        * with the ability to modify the variance in an arbitrary direction
2.  **Loss Function Evaluation:**
    * Evaluate the samples using a loss function.  This assigns a loss value to each sample.
3.  **Loss-Based Variance Analysis:**
    * Analyse how changes in the input samples relate to changes in the loss function.  This can be done by:
        * Calculating the gradient/Jacobian/difference of the loss function with respect to the input samples.
        * Using this gradient/Jacobian/difference information to construct a matrix (analogous to a covariance matrix) that describes how the loss function varies with changes in the input.
        * Performing principal component analysis on this matrix.  This identifies the directions in the input space that most significantly affect the loss function.
    * Identify a subset of components that exhibit high variance in the loss function.
4.  **Dimensionality Reduction:**
    * Reduce the dimensionality of the Gaussian distribution based on the identified components that most affect the loss function.
    * For components *not* identified as significant:
        * Reduce their influence or "squish" them by decreasing the corresponding variance. This effectively compresses the distribution along those dimensions.
    * For the identified high-variance components (those that significantly affect the loss function), keep their original variance.
5.  **2D Subspace Selection:**
    * Choose the 2D subspace spanned by the two principal components with the highest eigenvalues (i.e., the two directions of maximum variance *in the loss function*).
6.  **Subspace Scan:**
    * Perform a scan within the selected 2D subspace. This could involve:
        * Sampling more densely within this subspace.
        * Visualising the data projected onto this subspace.
        * Searching for specific features or patterns within this subspace (e.g., regions of high or low loss).

**Example Workflow (Randomised Search):**

1.  **Initial Sampling:**
    * Define a search space for the parameters of a distribution (e.g., mean and variance of the data). This defines the range of possible distributions.
    * Sample a set of candidate distributions by randomly selecting parameters from this search space.
2.  **Sample Generation and Evaluation:**
    * For each candidate distribution:
        * Generate samples from that distribution.
        * Evaluate the generated samples using a loss function.
3.  **Distribution Selection:**
    * Select the distribution that produced the "best" samples, based on the evaluation of the loss function.
4.  **Loss-Based Dimensionality Reduction:**
    * Calculate the gradient/Jacobian/difference of the loss function with respect to the samples generated from the selected distribution.
    * Use this information to perform a principal component analysis, identifying directions that most influence the loss.
    * Retain only the components that explain a significant portion of the variance in the loss function.
    * Adapt the distribution to reflect these principal components, e.g. using the 'squish' method described in the previous workflow.
5.  **Subspace Scan:**
    * Perform a scan within the selected 2D subspace. This could involve:
        * Sampling more densely within this subspace.
        * Visualising the data projected onto this subspace.
        * Searching for specific features or patterns within this subspace (e.g., regions of high or low loss).
