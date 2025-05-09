"""This module collects methods that scan a landscape along affine linear subspaces,
so that they can easily be plotted."""

from typing import Callable, List, Optional, Union

import numpy as np
from matplotlib import pyplot as plt

from .dr_tools import AffineSubspace, numeric_hessian


class LinearScan:
    """This object contains the results of a linear scan.

    Attributes:

        result: a grid of values sampled from a real valued function.

        subspace: the affine linear subspace along which the samples were taken.

        scope: tells you how far the subspace was scanned in each direction.
            shape is (number of directions, 2)

        func: optional attribute to record the function that was sampled.

    Methods:

        show: Plots the result of the scan, if it is 1 or 2 dimensional.

    """

    def __init__(
        self,
        result: np.ndarray,
        subspace: AffineSubspace,
        scope: np.ndarray,
        func: Optional[Callable[[np.ndarray], float]] = None,
    ):
        self.result = result
        self.subspace = subspace
        self.scope = scope
        self.func = func

    def show(self, **plot_kwargs) -> None:
        """This method plots the results of the scan, unless it has more than 2
        dimensions."""

        # 2D scan
        if self.result.ndim == 2:
            plt.imshow(
                np.transpose(self.result),
                extent=[
                    self.scope[0, 0],
                    self.scope[0, 1],
                    self.scope[1, 0],
                    self.scope[1, 1],
                ],
                **plot_kwargs,
            )
            plt.xlabel("first scan direction")
            plt.ylabel("second scan direction")

        # 1D scan
        elif self.result.ndim == 1:
            y = self.result
            x = np.linspace(
                self.scope[0, 0], self.scope[0, 1], len(self.result)
            )
            plt.plot(x, y, **plot_kwargs)
            plt.xlabel("scan direction")
            plt.ylabel("function value")

        # error for too many dimensions
        else:
            raise AttributeError(
                "Only scans of dimension 1 or 2 can be shown."
            )


class ScanCollection:
    """This object contains a collection of Linear scan objects.

    Attributes:

        scanlist: A list of LinearScan objects

    Method:

        show: plots all of the scans at once

    """

    def __init__(
        self,
        scanlist: List[LinearScan],
    ):
        self.scanlist = scanlist

    def show(
        self, showlist: Optional[List[int]] = None, **plot_kwargs
    ) -> None:
        """This method plots all the scans of the collection in one figure.
        All of them must be 1D for this to work.

        Input:

            showlist: The idices of the scans that are to be shown.
                For example [0,2] would show only the first and third scan.

        To display the legend execute matplotlib.pyplot.legend() after this method.
        """

        if showlist is None:
            showlist = range(len(self.scanlist))

        if self.scanlist[0].subspace.directions.shape[0] == 1:
            for i_scan in showlist:
                _plot_kwargs = {
                    **{"label": "direction " + str(i_scan)},
                    **plot_kwargs,
                }
                self.scanlist[i_scan].show(**_plot_kwargs)
        else:
            raise AttributeError(
                "Only scans of dimension 1 can be shown as collectives."
            )


class PathScan:
    """This object contains a 1D scan that is related to a path in the landscape.

    Attributes:

        path: A sequence of points in the landscape. (shape [num_points, dim])
            For example this could be a training trajectory.

        result: A flat array of loss values.

        mode: The method used to obtain the results. There should be the following:
            - raw (just every node of the path evaluated)
            - compressed (every node of the path evaluated given a minimal distance to the last evaluated point)
            - refined (every node of the path and some number of nodes in between two steps)
            - segmented (some number of nodes, equidistant on the path, probably wont include most nodes of the path)

        function: the function that was scanned
    """

    def __init__(
        self,
        result: np.ndarray,
        path: np.ndarray,
        mode: str,
        func: Optional[Callable[[np.ndarray], float]] = None,
    ):
        self.result = result
        self.path = path
        self.mode = mode
        self.func = func

    def show(self, **plot_kwargs) -> None:
        plt.plot(self.result, **plot_kwargs)


def landscape_scan_linear(
    func: Callable[[np.ndarray], float],
    subspace: AffineSubspace,
    scope: Union[np.ndarray, float] = 5,
    resolution: Optional[Union[int, np.ndarray]] = 10,
    pools: Optional[int] = 1,
) -> LinearScan:
    """This function scans a portion of an affine linear subspace of the higher
    dimensional lanscape created by func, with a specified resolution.

    Input:

        func: The function that defines the landscape.

        subspace: The affine linear subspace along which the scan is performed.

        scope: How far to scan in each direction of subspace.
        The size has to be (d_num,2), where for each direction the first entry is the
        beginning of the scope and the second is the end.
        If provided as float, the beginning will be -scope and the end +scope.

        resolution: How many samples to take in each direction of subspace.
        If provided as int, the resolution will be the same for each direction.

        pools: the number of pools to be used in the parallelization of the
        evaluation of func on the parameter grid. This is currently deactivated
        as it might not work as intended.

    Output:

        A LinearScan object.

    Notes:

        The total number of func calls is prod(resolution).

        The outermost values sampled are defined by scope.
        In particular the exact center of the subspace will only be sampled if all
        resolutions are odd.

    """

    # initalizing some important variables:

    d_num = subspace.directions.shape[0]
    d_dim = subspace.directions.shape[1]

    if not isinstance(scope, np.ndarray):
        scope = scope * np.append(-np.ones([d_num, 1]), np.ones([d_num, 1]), 1)

    if not (scope[:, 0] < scope[:, 1]).all():
        raise ValueError(
            """scope[id_d,0] must be strictly smaller than scope[id_d,1] for each
            direction."""
        )

    if np.isscalar(resolution):
        resolution = resolution * np.ones(d_num, dtype=int)

    # creating the grid of arguments to be scanned:
    # by first initializing every point as bottom_corner and then adding scaled grids
    # of all the direction vectors
    bottom_corner = (
        subspace.center.flatten()
        + np.sum(
            np.dot(np.diag(scope[:, 0]), subspace.directions), 0
        ).flatten()
    )
    grid = np.tile(bottom_corner, np.append(resolution, [1]))
    for id_d in range(d_num):
        steps_d = np.linspace(
            0, scope[id_d, 1] - scope[id_d, 0], resolution[id_d]
        )
        tile_d = np.multiply.outer(steps_d, subspace.directions[id_d, :])

        morph_d = np.ones(grid.ndim, dtype=np.int64)
        morph_d[-1] = d_dim
        morph_d[id_d] = resolution[id_d]
        tile_d = tile_d.reshape(morph_d)

        res_d = np.append(resolution, [1])
        res_d[id_d] = 1

        grid_d = np.tile(tile_d, res_d)

        grid = grid + grid_d

    # applying the function to all the values in the grid to get the scan:
    # this should be the most expensive step

    # used some tricks with reshape to write a paralellization friendly loop that
    # iterates over all the argument vectors in the grid

    res_total = np.prod(resolution)
    result = np.zeros(res_total)
    grid_r = grid.reshape(res_total, d_dim)

    # # parallelized (experimental)
    # with mp.Pool(pools) as p:
    #     result = p.map(func, grid_r)
    # result = np.array(result).reshape(resolution)

    # unparallelized
    for id_r in range(res_total):
        result[id_r] = func(grid_r[[id_r], :])
    result = np.array(result).reshape(resolution)

    return LinearScan(result=result, subspace=subspace, scope=scope)


def collective_scan_linear(
    func: Callable[[np.ndarray], float],
    subspace: AffineSubspace,
    scope: Union[np.ndarray, float] = 5,
    resolution: Optional[Union[int, np.ndarray]] = 10,
    pools: Optional[int] = 1,
) -> ScanCollection:
    """This functions creates a 1D scan
    in every direction of the provided subspace.

    Input:

        func: The function that defines the landscape.

        subspace: The affine linear subspace along which the scan is performed.

        scope: How far to scan in each direction of subspace.
            The size has to be (d_num,2), where for each direction the first entry
            is the beginning of the scope and the second is the end.
            If provided as float, the beginning will be -scope and the end +scope.
            resolution: How many samples to take in each direction of subspace.
            The total number of func calls is prod(resolution).

    Output:
        ScanCollection object that contains 1D scans for each direction of the subspace.

    """
    d_num = subspace.directions.shape[0]

    if not isinstance(scope, np.ndarray):
        scope = scope * np.append(-np.ones([d_num, 1]), np.ones([d_num, 1]), 1)

    if not (scope[:, 0] < scope[:, 1]).all():
        raise ValueError(
            """scope[id_d,0] must be strictly smaller
            than scope[id_d,1] for each direction."""
        )

    if isinstance(resolution, int):
        resolution = resolution * np.ones(d_num, dtype=int)

    # defining and immediately scanning all the 1D subspaces
    scanlist = []
    for i_scan in range(d_num):
        scanlist.append(
            landscape_scan_linear(
                func,
                AffineSubspace(
                    directions=subspace.directions[[i_scan], :],
                    center=subspace.center,
                ),
                scope=scope[[i_scan], :],
                resolution=resolution[i_scan],
                pools=pools,
            )
        )

    return ScanCollection(scanlist)


def hessian_scan(
    func: Callable[[np.ndarray], float],
    subspace: AffineSubspace,
    scope: Optional[Union[np.ndarray, float]] = 5,
    resolution: Optional[Union[int, np.ndarray]] = 10,
    epsilon: Optional[float] = 0.01,
    pools: Optional[int] = 1,
):
    """This function calculates the Hessian of func at the center of subspace
    and performs a collective scan in the directions of the eigenvectors.

    Input:

        func: The function that defines the landscape.

        subspace: The affine linear subspace along which the scan is performed.

        scope: How far to scan in each direction of subspace.
        The size has to be (d_num,2), where for each direction the first entry is the
        beginning of the scope and the second is the end.
        If provided as float, the beginning will be -scope and the end +scope.

        resolution: How many samples to take in each direction of subspace.
        If provided as int, the resolution will be the same for each direction.

    Output:

        The Hessian and a ScanCollection object.

    """

    H = numeric_hessian(func=func, subspace=subspace, epsilon=epsilon)
    H.calc_evs()
    subspace_H = AffineSubspace(
        directions=np.dot(H.eigenvectors.transpose(), subspace.directions),
        center=subspace.center,
    )

    scan_H = collective_scan_linear(
        func=func,
        subspace=subspace_H,
        scope=scope,
        resolution=resolution,
        pools=pools,
    )

    return scan_H, H


def pathscan(
    func: Callable[[np.ndarray], float],
    path: np.ndarray,
    mode: str,
    resolution: Optional[int] = 0,
    stepsize: Optional[float] = 0,
    pools: Optional[int] = 1,
) -> PathScan:
    l_p = path.shape[0]
    dim = path.shape[1]

    if mode == "raw":
        scanpath = path
    if mode == "refined":
        scanpath = np.zeros([(l_p - 1) * (1 + resolution) + 1, dim])
        for step_id in range(l_p - 1):
            for i_res in range(resolution + 1):
                scanpath[step_id * (resolution + 1) + i_res, :] = path[
                    step_id, :
                ] + (path[step_id + 1, :] - path[step_id, :]) * (i_res) / (
                    resolution + 1
                )
        scanpath[-1] = path[-1]
    if mode == "compressed":
        scanpath = np.zeros(shape=path.shape)
        scanpath[0, :] = path[0, :]
        cp = 1
        csp = 1
        acc_path = 0
        while cp < l_p:
            acc_path += np.linalg.norm(path[cp - 1, :] - path[cp, :])
            if acc_path >= stepsize:
                scanpath[csp, :] = path[cp, :]
                cp += 1
                csp += 1
                acc_path = 0
            else:
                cp += 1
        scanpath = scanpath[:csp, :]
    if mode == "segmented":
        total_path = 0
        for step_id in range(l_p - 1):
            total_path += np.linalg.norm(
                path[step_id, :] - path[step_id + 1, :]
            )
        stepsize = total_path / (resolution - 1)

        scanpath = np.zeros(shape=path.shape)
        scanpath[0, :] = path[0, :]
        cp = 1
        csp = 1
        acc_path = 0
        while cp < l_p:
            if (
                acc_path + np.linalg.norm(path[cp - 1, :] - path[cp, :])
                >= stepsize
            ):
                reststep = stepsize - acc_path
                scanpath[csp, :] = path[cp, :]
                cp += 1
                csp += 1
                acc_path = reststep
            else:
                cp += 1
        scanpath = scanpath[:csp, :]

    pass
