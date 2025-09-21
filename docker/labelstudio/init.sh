#!/bin/bash
label-studio init "Layout Model" \
  --label-config /label-studio/config/layout_labels.xml \
  --username $LABEL_STUDIO_USERNAME --password $LABEL_STUDIO_PASSWORD

label-studio init "OCR Model" \
  --label-config /label-studio/config/ocr_labels.xml \
  --username $LABEL_STUDIO_USERNAME --password $LABEL_STUDIO_PASSWORD