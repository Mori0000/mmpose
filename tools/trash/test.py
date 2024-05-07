# Copyright (c) OpenMMLab. All rights reserved.
import argparse
import os
import os.path as osp

import mmengine
from mmengine.config import Config, DictAction
from mmengine.hooks import Hook
from mmengine.runner import Runner

import pickle
import os
import copy
import json
import logging

'''

'''

def parse_args():                                                               # ここで引数をパースしている
    parser = argparse.ArgumentParser(                                           # argparse.ArgumentParser()でパーサーを作成
        description='MMPose test (and eval) model')                             # パーサーの説明を追加
    parser.add_argument('config', help='test config file path')                 # config引数を追加
    parser.add_argument('checkpoint', help='checkpoint file')                   # ckeckpoint引数を追加
    parser.add_argument(                                                        
        '--work-dir', help='the directory to save evaluation results')          # work-dir引数を追加 
    parser.add_argument('--out', help='the file to save metric results.')       # --out引数を追加
    parser.add_argument(
        '--dump',                                                               # --dump引数を追加
        type=str,                                                               # 引数の型を指定
        help='dump predictions to a pickle file for offline evaluation')        # ヘルプメッセージを追加
    parser.add_argument(
        '--cfg-options',                                                        # --cfg-options引数を追加
        nargs='+',                                                              # 引数の数を指定
        action=DictAction,                                                      # アクションを指定
        default={},                                                             # デフォルト値を指定
        help='override some settings in the used config, the key-value pair '   # ヘルプメッセージを追加
        'in xxx=yyy format will be merged into config file. For example, '
        "'--cfg-options model.backbone.depth=18 model.backbone.with_cp=True'")
    parser.add_argument(
        '--show-dir',
        # default='/home/moriki/PoseEstimation/mmpose/data/outputs/mmpose/show',    # ここのコメントアウト外せば、結果が保存される
        help='directory where the visualization images will be saved.')
    parser.add_argument(
        '--show',
        action='store_true',
        # default='/home/moriki/PoseEstimation/mmpose/data/outputs/mmpose/shows',
        help='whether to display the prediction results in a window.')
    parser.add_argument(
        '--interval',
        type=int,
        default=1,
        help='visualize per interval samples.')
    parser.add_argument(
        '--wait-time',
        type=float,
        default=1,
        help='display time of every window. (second)')
    parser.add_argument(
        '--launcher',
        choices=['none', 'pytorch', 'slurm', 'mpi'],
        default='none',
        help='job launcher')
    # When using PyTorch version >= 2.0.0, the `torch.distributed.launch`
    # will pass the `--local-rank` parameter to `tools/test.py` instead
    # of `--local_rank`.
    parser.add_argument('--local_rank', '--local-rank', type=int, default=0)
    parser.add_argument(
        '--badcase',
        action='store_true',
        default=False,
        help='whether analyze badcase in test')
    args = parser.parse_args()
    if 'LOCAL_RANK' not in os.environ:
        os.environ['LOCAL_RANK'] = str(args.local_rank)
    return args


def merge_args(cfg, args):                              # ここで引数をマージしている
    """Merge CLI arguments to config."""

    cfg.launcher = args.launcher                        # cfg.launcherにargs.launcherを代入
    cfg.load_from = args.checkpoint                     # cfg.load_fromにargs.checkpointを代入

    # -------------------- work directory --------------------
    # work_dir is determined in this priority: CLI > segment in file > filename
    if args.work_dir is not None:                                                   # args.work_dirがNoneでない場合
        # update configs according to CLI args if args.work_dir is not None
        cfg.work_dir = args.work_dir                                                # cfg.work_dirにargs.work_dirを代入
    elif cfg.get('work_dir', None) is None:                                         # cfg.get('work_dir', None)がNoneの場合
        # use config filename as default work_dir if cfg.work_dir is None
        cfg.work_dir = osp.join('./work_dirs',                                      # cfg.work_dirに'./work_dirs'とargs.configのベースネームを結合したものを代入
                                osp.splitext(osp.basename(args.config))[0])         # osp.splitext(osp.basename(args.config))[0]はargs.configのベースネームを取得している

    # -------------------- visualization --------------------
    if (args.show and not args.badcase) or (args.show_dir is not None):             # ここでargs.show_dirがNoneでない場合に、cfg.default_hooks.visualization.out_dirにargs.show_dirを代入している
        assert 'visualization' in cfg.default_hooks, \
            'PoseVisualizationHook is not set in the ' \
            '`default_hooks` field of config. Please set ' \
            '`visualization=dict(type="PoseVisualizationHook")`'

        cfg.default_hooks.visualization.enable = True                               # cfg.default_hooks.visualization.enableにTrueを代入
        cfg.default_hooks.visualization.show = False \
            if args.badcase else args.show                                          # cfg.default_hooks.visualization.showにFalseを代入
        if args.show:                                                               # args.showがTrueの場合
            cfg.default_hooks.visualization.wait_time = args.wait_time      # cfg.default_hooks.visualization.wait_timeにargs.wait_timeを代入
        cfg.default_hooks.visualization.out_dir = args.show_dir             # cfg.default_hooks.visualization.out_dirにargs.show_dirを代入
        cfg.default_hooks.visualization.interval = args.interval            # cfg.default_hooks.visualization.intervalにargs.intervalを代入

    # -------------------- badcase analyze --------------------
    if args.badcase:                                                        # args.badcaseがTrueの場合
        assert 'badcase' in cfg.default_hooks, \
            'BadcaseAnalyzeHook is not set in the ' \
            '`default_hooks` field of config. Please set ' \
            '`badcase=dict(type="BadcaseAnalyzeHook")`'

        cfg.default_hooks.badcase.enable = True                             # cfg.default_hooks.badcase.enableにTrueを代入
        cfg.default_hooks.badcase.show = args.show                          # cfg.default_hooks.badcase.showにargs.showを代入
        if args.show:                                                       # args.showがTrueの場合
            cfg.default_hooks.badcase.wait_time = args.wait_time            # cfg.default_hooks.badcase.wait_timeにargs.wait_timeを代入
        cfg.default_hooks.badcase.interval = args.interval                  # cfg.default_hooks.badcase.intervalにargs.intervalを代入

        metric_type = cfg.default_hooks.badcase.get('metric_type', 'loss')  # cfg.default_hooks.badcase.get('metric_type', 'loss')をmetric_typeに代入
        if metric_type not in ['loss', 'accuracy']:                         # metric_typeが['loss', 'accuracy']に含まれていない場合
            raise ValueError('Only support badcase metric type'             # ValueErrorを発生させる
                             "in ['loss', 'accuracy']")                     # エラーメッセージを追加

        if metric_type == 'loss':                                           # metric_typeが'loss'の場合
            if not cfg.default_hooks.badcase.get('metric'):                 # cfg.default_hooks.badcase.get('metric')がNoneの場合
                cfg.default_hooks.badcase.metric = cfg.model.head.loss      # cfg.default_hooks.badcase.metricにcfg.model.head.lossを代入
        else:                                                               # metric_typeが'loss'でない場合
            if not cfg.default_hooks.badcase.get('metric'):                 # cfg.default_hooks.badcase.get('metric')がNoneの場合
                cfg.default_hooks.badcase.metric = cfg.test_evaluator       # cfg.default_hooks.badcase.metricにcfg.test_evaluatorを代入

    # -------------------- Dump predictions --------------------
    if args.dump is not None:                                               # args.dumpがNoneでない場合
        assert args.dump.endswith(('.pkl', '.pickle')), \
            'The dump file must be a pkl file.'
        dump_metric = dict(type='DumpResults', out_file_path=args.dump)     # dump_metricに{'type': 'DumpResults', 'out_file_path': args.dump}を代入
        if isinstance(cfg.test_evaluator, (list, tuple)):                   # cfg.test_evaluatorがリストかタプルの場合
            cfg.test_evaluator = [*cfg.test_evaluator, dump_metric]         # cfg.test_evaluatorにcfg.test_evaluatorとdump_metricを結合したものを代入
        else:
            cfg.test_evaluator = [cfg.test_evaluator, dump_metric]          # cfg.test_evaluatorに[cfg.test_evaluator, dump_metric]を代入

    # -------------------- Other arguments --------------------
    if args.cfg_options is not None:                                        # args.cfg_optionsがNoneでない場合
        cfg.merge_from_dict(args.cfg_options)                               # cfg.merge_from_dict(args.cfg_options)を実行

    return cfg


class CustomRunner(Runner):
    @classmethod
    def from_cfg(cls, cfg) -> 'Runner':
        cfg = copy.deepcopy(cfg)
        runner = cls(
            model=cfg['model'],
            work_dir=cfg['work_dir'],
            train_dataloader=cfg.get('train_dataloader'),
            val_dataloader=cfg.get('val_dataloader'),
            test_dataloader=cfg.get('test_dataloader'),
            train_cfg=cfg.get('train_cfg'),
            val_cfg=cfg.get('val_cfg'),
            test_cfg=cfg.get('test_cfg'),
            auto_scale_lr=cfg.get('auto_scale_lr'),
            optim_wrapper=cfg.get('optim_wrapper'),
            param_scheduler=cfg.get('param_scheduler'),
            val_evaluator=cfg.get('val_evaluator'),
            test_evaluator=cfg.get('test_evaluator'),
            default_hooks=cfg.get('default_hooks'),
            custom_hooks=cfg.get('custom_hooks'),
            data_preprocessor=cfg.get('data_preprocessor'),
            load_from=cfg.get('load_from'),
            resume=cfg.get('resume', False),
            launcher=cfg.get('launcher', 'none'),
            env_cfg=cfg.get('env_cfg', dict(dist_cfg=dict(backend='nccl'))),
            log_processor=cfg.get('log_processor'),
            log_level=cfg.get('log_level', 'INFO'),
            visualizer=cfg.get('visualizer'),
            default_scope=cfg.get('default_scope', 'mmengine'),
            randomness=cfg.get('randomness', dict(seed=None)),
            experiment_name=cfg.get('experiment_name'),
            cfg=cfg,
        )
        return runner


    def test(self) -> dict:
        logging.info('Start running test')
        if self._test_loop is None:
            logging.info('No test loop')
            raise RuntimeError(
                '`self._test_loop` should not be None when calling test '
                'method. Please provide `test_dataloader`, `test_cfg` and '
                '`test_evaluator` arguments when initializing runner.')
        logging.info('--------------------------Start build test loop--------------------------')
        self._test_loop = self.build_test_loop(self._test_loop)  # type: ignore
        logging.info('--------------------------Start call hook--------------------------')
        self.call_hook('before_run')
        logging.info('--------------------------Start load or resume--------------------------')
        self.load_or_resume()
        logging.info('--------------------------Start run--------------------------')
        metrics = self.test_loop.run()  # type: ignore
        logging.info('--------------------------Start call hook--------------------------')
        self.call_hook('after_run')
        logging.info('--------------------------End running test--------------------------')
        return metrics

    def call_hook(self, fn_name: str, **kwargs) -> None:
        """Call all hooks.

        Args:
            fn_name (str): The function name in each hook to be called, such as
                "before_train_epoch".
            **kwargs: Keyword arguments passed to hook.
        """
        for hook in self._hooks:
            # support adding additional custom hook methods
            if hasattr(hook, fn_name):
                try:
                    getattr(hook, fn_name)(self, **kwargs)
                except TypeError as e:
                    raise TypeError(f'{e} in {hook}') from None
    
    def after_test_epoch(self, flow='test', metrics=None):
        if hasattr(super(), 'after_test_epoch'):
            super().after_test_epoch(flow, metrics)
        processed_metrics = self.process_metrics(metrics)
        self.save_processed_metrics(processed_metrics)
    def process_metrics(self, metrics):
        return metrics


    def save_processed_metrics(self, metrics):
        save_dir = '/home/moriki/PoseEstimation/mmpose/outputs_models'
        file_path = os.path.join(save_dir, 'processed_metrics.json')  # JSONファイルとして保存
        try:
            os.makedirs(save_dir, exist_ok=True)  # ディレクトリが存在しない場合は作成
            with open(file_path, 'w') as f:  # ファイルをテキストモードで開く
                json.dump(metrics, f, indent=4)  # JSON形式でデータを書き込み
            print(f"Metrics saved to {file_path}")
        except Exception as e:
            print(f"Failed to save metrics: {e}")


def main():
    logging.basicConfig(
        filename='example.log',  # ログを保存するファイル名
        filemode='a',            # 'a' は追記モード、'w' は上書きモード
        level=logging.DEBUG,     # ログレベル
        format='%(asctime)s - %(levelname)s - %(message)s'  # ログのフォーマット
    )
    args = parse_args()
    cfg = Config.fromfile(args.config)
    cfg = merge_args(cfg, args)
    runner = CustomRunner.from_cfg(cfg)
    metrics = runner.test()
    runner.after_test_epoch(metrics)

if __name__ == '__main__':
    main()
