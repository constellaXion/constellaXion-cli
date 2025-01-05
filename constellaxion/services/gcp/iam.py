from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth import default
from google.auth.exceptions import RefreshError


def create_service_account(project_id):
    """
    Create a service account and assign roles.

    Args:
        project_id (str): GCP Project ID.
    """
    roles = ['roles/aiplatform.user', 'roles/storage.admin']
    service_account_email = f"constellaxion-admin@{project_id}.iam.gserviceaccount.com"

    try:
        # Get credentials
        credentials, _ = default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"])
        iam_service = build('iam', 'v1', credentials=credentials)

        # Create service account
        try:
            iam_service.projects().serviceAccounts().create(
                name=f"projects/{project_id}",
                body={
                    "accountId": 'constellaxion-admin',
                    "serviceAccount": {
                        "displayName": 'Constellaxion Admin',
                    },
                },
            ).execute()
            print(f"Service account created: {service_account_email}")
        except Exception as e:
            # Handle specific errors
            if hasattr(e, 'resp') and e.resp.status == 409:
                print(
                    "ConstellaXion Admin Service Account already exists. Continuing...")
            else:
                raise

        # Assign project-level roles
        assign_project_roles(project_id, service_account_email, roles)
        return service_account_email

    except RefreshError as e:
        print("Error: Could not refresh credentials. Please ensure you are authenticated.")
        print(f"Details: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


def assign_project_roles(project_id, service_account_email, roles):
    """
    Assign project-level roles to a service account, skipping roles that are already assigned.

    Args:
        project_id (str): GCP Project ID.
        service_account_email (str): Email of the service account.
        roles (list): List of roles to assign.
    """
    credentials, _ = default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    cloud_resource_manager = build(
        'cloudresourcemanager', 'v1', credentials=credentials
    )

    # Get the current IAM policy for the project
    policy = cloud_resource_manager.projects().getIamPolicy(
        resource=project_id, body={}
    ).execute()

    # Extract existing bindings
    bindings = policy.get("bindings", [])
    for role in roles:
        # Check if the role is already assigned
        binding = next((b for b in bindings if b["role"] == role), None)
        if binding:
            members = binding.get("members", [])
            if f"serviceAccount:{service_account_email}" in members:
                print(
                    f"Role {role} already assigned to {service_account_email}. Skipping...")
                continue
            else:
                # Add the service account to the existing binding
                binding["members"].append(
                    f"serviceAccount:{service_account_email}")
        else:
            # Create a new binding if the role is not in the policy
            bindings.append({
                "role": role,
                "members": [f"serviceAccount:{service_account_email}"]
            })

    # Update the policy with the modified bindings
    policy["bindings"] = bindings

    # Push the updated policy back to GCP
    updated_policy = cloud_resource_manager.projects().setIamPolicy(
        resource=project_id, body={"policy": policy}
    ).execute()

    print(f"Roles assigned successfully: {roles}")
