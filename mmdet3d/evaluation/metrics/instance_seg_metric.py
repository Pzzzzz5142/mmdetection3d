# Copyright (c) OpenMMLab. All rights reserved.
import warnings
from typing import Optional, Sequence

from mmengine.logging import MMLogger, print_log
from mmeval.metrics import InstanceSeg
from terminaltables import AsciiTable

from mmdet3d.registry import METRICS


@METRICS.register_module()
class InstanceSegMetric(InstanceSeg):
    """3D instance segmentation evaluation metric.

    Args:
        dataset_meta (dict): Provide dataset meta information.
        dist_backend (str, optional): The distributed backend name want to get.
            if None, return the default distributed backend.
    """

    def __init__(self,
                 dataset_meta: dict,
                 dist_backend: Optional[str] = None,
                 collect_device: Optional[str] = None,
                 prefix: Optional[str] = None,
                 **kwargs):
        if collect_device is not None:
            warnings.warn(
                'DeprecationWarning: The `collect_device` parameter of '
                '`InstanceSegMetric` is deprecated, use `dist_backend instead.'
            )
        if prefix is not None:
            warnings.warn('DeprecationWarning: The `prefix` parameter of '
                          '`InstanceSegMetric` is deprecated.')
        super(InstanceSegMetric, self).__init__(
            dataset_meta=dataset_meta, dist_backend=dist_backend, **kwargs)

    def process(self, data_batch: dict, data_samples: Sequence[dict]) -> None:
        """Process one batch of data samples and predictions.

        The processed results should be stored in ``self.results``,
        which will be used to compute the metrics when all batches
        have been processed.

        Args:
            data_batch (dict): A batch of data from the dataloader.
            data_samples (Sequence[dict]): A batch of outputs from
                the model.
        """
        pred = []
        gt = []
        for data_sample in data_samples:
            pred_3d = data_sample['pred_pts_seg']
            eval_ann_info = data_sample['eval_ann_info']
            cpu_pred_3d = {
                k: v.clone().cpu().numpy()
                for k, v in pred_3d.items()
            }
            cpu_eval_ann_info = {
                k: v.clone().cpu().numpy()
                for k, v in eval_ann_info.items()
            }
            for k, v in pred_3d.items():
                if hasattr(v, 'to'):
                    cpu_pred_3d[k] = v.to('cpu').clone().numpy()
                else:
                    cpu_pred_3d[k] = v.clone().numpy()
            pred.append(cpu_pred_3d)
            gt.append(cpu_eval_ann_info)
        self.add(pred, gt)

    def evaluate(self, *args, **kwargs):
        """Evaluate the model performance of the whole dataset after processing
        all batches."""
        logger: MMLogger = MMLogger.get_current_instance()

        metrics = self.compute(*args, **kwargs)
        header = ['classes', 'AP_0.25', 'AP_0.50', 'AP']
        rows = []
        for label, data in metrics['classes'].items():
            aps = [data['ap25%'], data['ap50%'], data['ap']]
            rows.append([label] + [f'{ap:.4f}' for ap in aps])
        aps = metrics['all_ap_25%'], metrics['all_ap_50%'], metrics['all_ap']
        footer = ['Overall'] + [f'{ap:.4f}' for ap in aps]
        table = AsciiTable([header] + rows + [footer])
        table.inner_footing_row_border = True
        print_log('\n' + table.table, logger=logger)

        self.reset()

        return metrics
