#!/bin/bash

# Load configuration from config.json
CONFIG_FILE="config.json"

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "Error: Configuration file '$CONFIG_FILE' not found!"
  exit 1
fi

get_config_value() {
  grep -oP '"'"$1"'"\s*:\s*"\K[^"]+' "$CONFIG_FILE"
}

BASE_BUCKET_NAME=$(get_config_value "BASE_BUCKET_NAME")
REGION=$(get_config_value "REGION")
COMPONENT_NAME=$(get_config_value "COMPONENT_NAME")
VERSION=$(get_config_value "VERSION")
TARGET_NAME=$(get_config_value "TARGET_NAME")
ARTIFACTS_PATH="./BleGatewayComponent/artifacts/$COMPONENT_NAME/$VERSION"
RECIPES_PATH="./BleGatewayComponent/recipes"

# Echo configuration
echo -e "Target Name:\t$TARGET_NAME"
echo -e "Bucket Name:\t$BASE_BUCKET_NAME"
echo -e "AWS Region:\t$REGION"
echo -e "Version:\t$VERSION"
echo -e "Artifacts Path:\t$ARTIFACTS_PATH"
echo -e "Recipes Path:\t$RECIPES_PATH"

# Generate the bucket name using the account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
BUCKET_NAME="${BASE_BUCKET_NAME}-${ACCOUNT_ID}"

# Check if the bucket exists and create it if necessary
if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
  echo "Bucket $BUCKET_NAME already exists."
else
  echo "Creating bucket $BUCKET_NAME..."
  aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION" \
    --create-bucket-configuration LocationConstraint="$REGION"
fi

# Upload files to S3
echo "Uploading artifacts to S3..."
aws s3 cp "$ARTIFACTS_PATH/BleGateway.py" "s3://$BUCKET_NAME/$COMPONENT_NAME/$VERSION/"
aws s3 cp "$ARTIFACTS_PATH/install.sh" "s3://$BUCKET_NAME/$COMPONENT_NAME/$VERSION/"

# Verify uploads
echo "Verifying uploads..."
if aws s3 ls "s3://$BUCKET_NAME/$COMPONENT_NAME/$VERSION/BleGateway.py" >/dev/null 2>&1 && \
   aws s3 ls "s3://$BUCKET_NAME/$COMPONENT_NAME/$VERSION/install.sh" >/dev/null 2>&1; then
    echo "Artifacts uploaded successfully."
else
    echo "Error: One or more artifacts failed to upload. Aborting deployment."
    exit 1
fi

# Update the bucket name and version in the recipe
UPDATED_RECIPE_PATH="$RECIPES_PATH/com.example.BleGateway-$VERSION.yaml"
sed -e "s/{{BUCKET_NAME}}/$BUCKET_NAME/g" \
    -e "s/{{VERSION}}/$VERSION/g" \
    -e "s/{{COMPONENT_NAME}}/$COMPONENT_NAME/g" \
    "$RECIPES_PATH/com.example.BleGateway-TEMPLATE.yaml" > "$UPDATED_RECIPE_PATH"
echo "Updated recipe created: $UPDATED_RECIPE_PATH"

# Create the component in Greengrass
echo "Creating the component in Greengrass..."
aws greengrassv2 create-component-version \
  --inline-recipe fileb://"$UPDATED_RECIPE_PATH"

# Deploy the component
echo "Deploying the component to the Greengrass target..."

# Check if the TARGET_NAME corresponds to a Thing or a Thing Group
if aws iot describe-thing --thing-name "$TARGET_NAME" >/dev/null 2>&1; then
    # If it’s a Thing, use the Thing ARN
    TARGET_ARN="arn:aws:iot:$REGION:$ACCOUNT_ID:thing/$TARGET_NAME"
elif aws iot describe-thing-group --thing-group-name "$TARGET_NAME" >/dev/null 2>&1; then
    # If it’s a Thing Group, use the Thing Group ARN
    TARGET_ARN="arn:aws:iot:$REGION:$ACCOUNT_ID:thinggroup/$TARGET_NAME"
else
    echo "Error: TARGET_NAME is neither a valid Thing nor a Thing Group."
    exit 1
fi

# Create the Greengrass deployment
aws greengrassv2 create-deployment \
  --target "$TARGET_ARN" \
  --components "{\"$COMPONENT_NAME\": {\"componentVersion\": \"$VERSION\"}}"


## Cleanup the updated recipe (optional)
# rm "$UPDATED_RECIPE_PATH"
echo "Deployment completed successfully!"
