# Visualization

- [Browse Dataset](#browse-dataset)
- [Visualizer Hook](#visualizer-hook)

## Browse Dataset

`tools/analysis_tools/browse_dataset.py` helps the user to browse a pose dataset visually, or save the image to a designated directory.

```shell
python tools/misc/browse_dataset.py ${CONFIG} [-h] [--output-dir ${OUTPUT_DIR}] [--not-show] [--phase ${PHASE}] [--mode ${MODE}] [--show-interval ${SHOW_INTERVAL}]
```

| ARGS                             | Description                                                                                                                                           |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CONFIG`                         | The path to the config file.                                                                                                                          |
| `--output-dir OUTPUT_DIR`        | The target folder to save visualization results. If not specified, the visualization results will not be saved.                                       |
| `--not-show`                     | Do not show the visualization results in an external window.                                                                                          |
| `--phase {train, val, test}`     | Options for dataset.                                                                                                                                  |
| `--mode {original, transformed}` | Specify the type of visualized images. `original` means to show images without pre-processing; `transformed` means to show images are pre-processing. |
| `--show-interval SHOW_INTERVAL`  | Time interval between visualizing two images.                                                                                                         |

For instance, users who want to visualize images and annotations in COCO dataset may use:

```shell
python tools/misc/browse_dataset.py configs/body_2d_keypoint/topdown_heatmap/coco/td-hm_hrnet-w32_8xb64-e210_coco-256x192.py --mode original
```

The bounding boxes and keypoints will be plotted on the original image. Following is an example:
![original_coco](https://user-images.githubusercontent.com/26127467/187383698-7e518f21-b4cc-4712-9e97-99ddd8f0e437.jpg)

The original images need to be processed before being fed into models. To visualize pre-processed images and annotations, users need to modify the `mode` parameter to `transformed`. For example:

```shell
python tools/misc/browse_dataset.py configs/body_2d_keypoint/topdown_heatmap/coco/td-hm_hrnet-w32_8xb64-e210_coco-256x192.py --mode transformed
```

Here is a processed sample

![transformed_coco](https://user-images.githubusercontent.com/26127467/187386652-bd47335d-797c-4e8c-b823-2a4915f9812f.jpg)

The heatmap target will be visualized together if it is generated in the pipeline.

## Visualizer Hook

During validation and testing, users can specify certain parameters to visualize the output of trained models.

To visualize in external window during testing:

```shell
python tools/test.py ${CONFIG} ${CHECKPOINT} --show
```

During validation:

```shell
python tools/train.py ${CONFIG} --work-dir ${WORK_DIR} --show --interval ${INTERVAL}
```

It is suggested to use large `INTERVAL` (e.g., 50) if users want to visualize during validation, since the wait time for each visualized instance will make the validation process very slow.

To save visualization results in `SHOW_DIR` during testing:

```shell
python tools/test.py ${CONFIG} ${CHECKPOINT} --show-dir=${SHOW_DIR}
```

During validation:

```shell
python tools/train.py ${CONFIG} --work-dir ${WORK_DIR} --show-dir=${SHOW_DIR}
```

More details about visualization hook arguments can be found in [train_and_test](./train_and_test.md).

If you use a heatmap-based method and want to visualize predicted heatmaps, you can manually specify `output_heatmaps=True` for `model.test_cfg` in config file. Another way is to add `--cfg-options='model.test_cfg.output_heatmaps=True'` at the end of your command.

Visualization example (top: decoded keypoints; bottom: predicted heatmap):
![vis_pred](https://user-images.githubusercontent.com/26127467/187578902-30ef7bb0-9a93-4e03-bae0-02aeccf7f689.jpg)

For top-down models, each sample only contains one instance. So there will be multiple visualization results for each image.