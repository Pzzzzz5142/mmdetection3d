import numpy as np

from mmdet3d.core.bbox import DepthInstance3DBoxes
from mmdet.datasets import DATASETS
from .custom_3d import Custom3DDataset


@DATASETS.register_module()
class SUNRGBDDataset(Custom3DDataset):

    CLASSES = ('bed', 'table', 'sofa', 'chair', 'toilet', 'desk', 'dresser',
               'night_stand', 'bookshelf', 'bathtub')

    def __init__(self,
                 data_root,
                 ann_file,
                 pipeline=None,
                 classes=None,
                 modality=None,
                 box_type_3d='Depth',
                 filter_empty_gt=True,
                 test_mode=False):
        super().__init__(
            data_root=data_root,
            ann_file=ann_file,
            pipeline=pipeline,
            classes=classes,
            modality=modality,
            box_type_3d=box_type_3d,
            filter_empty_gt=filter_empty_gt,
            test_mode=test_mode)

    def get_ann_info(self, index):
        # Use index to get the annos, thus the evalhook could also use this api
        info = self.data_infos[index]
        if info['annos']['gt_num'] != 0:
            gt_bboxes_3d = info['annos']['gt_boxes_upright_depth'].astype(
                np.float32)  # k, 6
            gt_labels_3d = info['annos']['class'].astype(np.long)
        else:
            gt_bboxes_3d = np.zeros((0, 7), dtype=np.float32)
            gt_labels_3d = np.zeros((0, ), dtype=np.long)

        # to target box structure
        gt_bboxes_3d = DepthInstance3DBoxes(
            gt_bboxes_3d, origin=(0.5, 0.5, 0.5)).convert_to(self.box_mode_3d)

        anns_results = dict(
            gt_bboxes_3d=gt_bboxes_3d, gt_labels_3d=gt_labels_3d)
        return anns_results