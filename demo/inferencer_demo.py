# Copyright (c) OpenMMLab. All rights reserved.
from argparse import ArgumentParser
from typing import Dict
import sys
import os

sys.path.append('/home/moriki/PoseEstimation/mmpose/')

from mmpose.apis.inferencers import MMPoseInferencer, get_model_aliases

filter_args = dict(bbox_thr=0.3, nms_thr=0.3, pose_based_nms=False)
POSE2D_SPECIFIC_ARGS = dict(
    yoloxpose=dict(bbox_thr=0.01, nms_thr=0.65, pose_based_nms=True),
    rtmo=dict(bbox_thr=0.1, nms_thr=0.65, pose_based_nms=True),
)


def parse_args():                                    # ここで引数をパースしている
    parser = ArgumentParser()                       # ArgumentParser()でパーサーを作成
    parser.add_argument(                            # 引数を追加
        'inputs',                                       # 引数名を追加
        type=str,
        nargs='?',
        help='Input image/video path or folder path.')
    # init args
    parser.add_argument(                # 引数を追加
        '--pose2d',                     # 引数名を追加
        type=str,
        default=None,
        help='Pretrained 2D pose estimation algorithm. It\'s the path to the '
        'config file or the model name defined in metafile.')
    parser.add_argument(
        '--pose2d-weights',
        type=str,
        default=None,
        help='Path to the custom checkpoint file of the selected pose model. '
        'If it is not specified and "pose2d" is a model name of metafile, '
        'the weights will be loaded from metafile.')
    # parser.add_argument(
    #     '--output_heatmaps',                #! 追加したところ
    #     action='store_true',
    #     default=False,
    #     help='Flag to visualize predicted heatmaps. If enabled, the model will output heatmaps.')  
    parser.add_argument(
        '--pose3d',
        type=str,
        default=None,
        help='Pretrained 3D pose estimation algorithm. It\'s the path to the '
        'config file or the model name defined in metafile.')
    parser.add_argument(
        '--pose3d-weights',
        type=str,
        default=None,
        help='Path to the custom checkpoint file of the selected pose model. '
        'If it is not specified and "pose3d" is a model name of metafile, '
        'the weights will be loaded from metafile.')
    parser.add_argument(
        '--det-model',
        type=str,
        default=None,
        help='Config path or alias of detection model.')
    parser.add_argument(
        '--det-weights',
        type=str,
        default=None,
        help='Path to the checkpoints of detection model.')
    parser.add_argument(
        '--det-cat-ids',
        type=int,
        nargs='+',
        default=0,
        help='Category id for detection model.')
    parser.add_argument(
        '--scope',
        type=str,
        default='mmpose',
        help='Scope where modules are defined.')
    parser.add_argument(
        '--device',
        type=str,
        default=None,
        help='Device used for inference. '
        'If not specified, the available device will be automatically used.')
    parser.add_argument(
        '--show-progress',
        action='store_true',
        help='Display the progress bar during inference.')

    # The default arguments for prediction filtering differ for top-down
    # and bottom-up models. We assign the default arguments according to the
    # selected pose2d model
    args, _ = parser.parse_known_args()                             # 引数をパース
    for model in POSE2D_SPECIFIC_ARGS:                              # モデルを取得
        if model in args.pose2d:                                    # モデルがargs.pose2dにある場合
            filter_args.update(POSE2D_SPECIFIC_ARGS[model])         # filter_argsにPOSE2D_SPECIFIC_ARGS[model]を追加
            break

    # call args
    parser.add_argument(                # 引数を追加
        '--show',                       # 引数名を追加
        action='store_true',            # アクションを追加
        help='Display the image/video in a popup window.')          # ヘルプメッセージを追加
    parser.add_argument(                # 引数を追加
        '--draw-bbox',
        action='store_true',
        help='Whether to draw the bounding boxes.')
    parser.add_argument(
        '--draw-heatmap',
        action='store_true',
        default=True,
        help='Whether to draw the predicted heatmaps.')
    parser.add_argument(
        '--bbox-thr',
        type=float,
        default=filter_args['bbox_thr'],
        help='Bounding box score threshold')
    parser.add_argument(
        '--nms-thr',
        type=float,
        default=filter_args['nms_thr'],
        help='IoU threshold for bounding box NMS')
    parser.add_argument(
        '--pose-based-nms',
        type=lambda arg: arg.lower() in ('true', 'yes', 't', 'y', '1'),
        default=filter_args['pose_based_nms'],
        help='Whether to use pose-based NMS')
    parser.add_argument(
        '--kpt-thr', type=float, default=0.3, help='Keypoint score threshold')
    parser.add_argument(
        '--tracking-thr', type=float, default=0.3, help='Tracking threshold')
    parser.add_argument(
        '--use-oks-tracking',
        default=False,
        action='store_true',
        help='Whether to use OKS as similarity in tracking')
    parser.add_argument(
        '--disable-norm-pose-2d',
        action='store_true',
        help='Whether to scale the bbox (along with the 2D pose) to the '
        'average bbox scale of the dataset, and move the bbox (along with the '
        '2D pose) to the average bbox center of the dataset. This is useful '
        'when bbox is small, especially in multi-person scenarios.')
    parser.add_argument(
        '--disable-rebase-keypoint',
        action='store_true',
        default=False,
        help='Whether to disable rebasing the predicted 3D pose so its '
        'lowest keypoint has a height of 0 (landing on the ground). Rebase '
        'is useful for visualization when the model do not predict the '
        'global position of the 3D pose.')
    parser.add_argument(
        '--num-instances',
        type=int,
        default=1,
        help='The number of 3D poses to be visualized in every frame. If '
        'less than 0, it will be set to the number of pose results in the '
        'first frame.')
    parser.add_argument(
        '--radius',
        type=int,
        default=3,
        help='Keypoint radius for visualization.')
    parser.add_argument(
        '--thickness',
        type=int,
        default=1,
        help='Link thickness for visualization.')
    parser.add_argument(
        '--skeleton-style',
        default='mmpose',
        type=str,
        choices=['mmpose', 'openpose'],
        help='Skeleton style selection')
    parser.add_argument(
        '--draw-heatmaps',
        action='store_true',
        default=True,
        help='Whether to draw the predicted heatmaps.')
    parser.add_argument(
        '--black-background',
        default=False,
        action='store_true',
        help='Plot predictions on a black image')
    parser.add_argument(
        '--vis-out-dir',
        default='/home/moriki/PoseEstimation/mmpose/outputs/inferencer-vis',
        type=str,
        help='Directory for saving visualized results.')
    parser.add_argument(
        '--pred-out-dir',
        type=str,
        default='/home/moriki/PoseEstimation/mmpose/outputs/heatmap',      #! 追加したところ
        help='Directory for saving inference results.')
    parser.add_argument(
        '--show-alias',
        default=True,
        action='store_true',
        help='Display all the available model aliases.')

    call_args = vars(parser.parse_args())

    init_kws = [
        'pose2d', 'pose2d_weights', 'scope', 'device', 'det_model',
        'det_weights', 'det_cat_ids', 'pose3d', 'pose3d_weights',
        'show_progress'
    ]
    # breakpoint()
    init_args = {}                                      # init_argsを空の辞書で初期化
    for init_kw in init_kws:                            # init_kwsを取得
        print('---------------------------------------------')
        print('init_kw:', init_kw)
        init_args[init_kw] = call_args.pop(init_kw)     # init_argsにinit_kwを追加

    print('==============================================')
    print('call_args:', call_args)
    print('==============================================')
    
    display_alias = call_args.pop('show_alias')         # call_argsから'show_alias'を取得

    return init_args, call_args, display_alias


def display_model_aliases(model_aliases: Dict[str, str]) -> None:
    """
    Display the available model aliases and their corresponding model names.
    使用可能なモデルのエイリアスとそれに対応するモデル名を表示します。
    """
    aliases = list(model_aliases.keys())
    max_alias_length = max(map(len, aliases))
    print(f'{"ALIAS".ljust(max_alias_length+2)}MODEL_NAME')
    for alias in sorted(aliases):
        print(f'{alias.ljust(max_alias_length+2)}{model_aliases[alias]}')

from mmcv.image import imread

from mmpose.apis import inference_topdown, init_model
from mmpose.registry import VISUALIZERS
from mmpose.structures import merge_data_samples

def main():
    init_args, call_args, display_alias = parse_args()
    inferencer = MMPoseInferencer(**init_args)
    print('---------------------------------')
    print('init_args:', init_args)
    print('---------------------------------')
    print('call_args:', call_args)
    print('---------------------------------')
    print('display_alias:', display_alias)
    print('---------------------------------')

    model_cfg = 'configs/body_2d_keypoint/rtmpose/coco/rtmpose-m_8xb256-420e_coco-256x192.py'
    ckpt = 'https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/rtmpose-m_simcc-body7_pt-body7-halpe26_700e-256x192-4d3e73dd_20230605.pth'
    device = 'cuda:0'

    model = init_model(model_cfg, ckpt, device=device)

    visualizer = VISUALIZERS.build(model.cfg.visualizer)

    for _ in inferencer(**call_args):
        pass

# def main():
#     # Parse the initial arguments from command line
#     init_args, call_args, display_alias = parse_args()

#     # Define dataset path (make sure this path is correct and accessible)
#     dataset_path = '/home/moriki/PoseEstimation/mmpose/data/crowdpose/images'

#     # Create the inferencer instance outside the loop to avoid repeated instantiation
#     inferencer = MMPoseInferencer(**init_args)

#     for i in [3, 4]:
#         image_id = 100000 + i
#         image_path = os.path.join(dataset_path, f'{image_id}.jpg')

#         # Check if the image file exists
#         if not os.path.exists(image_path):
#             continue  # Skip this iteration if the file does not exist

#         # Set the current input image path
#         call_args['inputs'] = image_path
        
#         # If the flag to display aliases is set, display them and skip the rest
#         if display_alias:
#             model_aliases = get_model_aliases(init_args['scope'])
#             display_model_aliases(model_aliases)
#             continue  # Skip processing if only displaying aliases

#         # Process the image and collect predictions
#         preds = []
#         results = inferencer(inputs=call_args['inputs'], batch_size=1, out_dir='/home/moriki/PoseEstimation/mmpose/outputs/heatmap-img')
#         for result in results:
#             preds.append(result)
        
#         # Visualize the predictions
#         inferencer.visualize(inputs=call_args['inputs'], preds=preds, **call_args)

if __name__ == "__main__":
    main()
