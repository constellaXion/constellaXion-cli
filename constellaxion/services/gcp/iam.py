"""
This module provides functions for managing IAM roles and service accounts in GCP.
"""

from google.auth import default
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.id_token import verify_oauth2_token
from googleapiclient.discovery import Resource, build


def create_service_account(project_id: str) -> str:
    """
    Create a service account and assign roles.

    Args:
        project_id (str): GCP Project ID.
    """
    roles = ["roles/aiplatform.user", "roles/storage.admin"]
    service_account_email = f"constellaxion-admin@{project_id}.iam.gserviceaccount.com"

    try:
        # Get credentials
        credentials, _ = default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )

        iam_service: Resource = build("iam", "v1", credentials=credentials)

        # Extract the email from credentials info
        user_email = get_logged_in_user_email()

        # Create service account
        try:
            iam_service.projects().serviceAccounts().create(
                name=f"projects/{project_id}",
                body={
                    "accountId": "constellaxion-admin",
                    "serviceAccount": {
                        "displayName": "Constellaxion Admin",
                    },
                },
            ).execute()
            print(f"Service account created: {service_account_email}")
        except Exception as e:
            # Handle specific errors
            if hasattr(e, "resp") and e.resp.status == 409:
                print(
                    "ConstellaXion Admin Service Account already exists. Continuing..."
                )
            else:
                raise

        # Assign project-level roles
        assign_project_roles(project_id, service_account_email, roles)

        # Allow user to act as the service account
        assign_impersonation_role(project_id, service_account_email, user_email)

        return service_account_email

    except RefreshError as e:
        print(
            "Error: Could not refresh credentials. Please ensure you are authenticated."
        )
        print(f"Details: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


def get_logged_in_user_email():
    """
    Get the email of the currently authenticated user.

    Returns:
        str: The email of the authenticated user.
    """
    try:
        # Get default credentials
        credentials, _ = default()

        # Refresh the credentials to get a valid token
        credentials.refresh(Request())

        # Get the ID token
        if not hasattr(credentials, "id_token") or not credentials.id_token:
            raise ValueError("No ID token found in credentials.")

        # Decode the ID token to extract the email
        id_info = verify_oauth2_token(credentials.id_token, Request())
        email = id_info.get("email")
        if not email:
            raise ValueError("Email not found in ID token.")

        return email
    except Exception as e:
        print(f"Error retrieving user email: {e}")
        raise


def assign_project_roles(project_id, service_account_email, roles):
    """
    Assign project-level roles to a service account, skipping roles that are already assigned.

    Args:
        project_id (str): GCP Project ID.
        service_account_email (str): Email of the service account.
        roles (list): List of roles to assign.
    """
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    cloud_resource_manager = build(
        "cloudresourcemanager", "v1", credentials=credentials
    )

    # Get the current IAM policy for the project
    policy = (
        cloud_resource_manager.projects()
        .getIamPolicy(resource=project_id, body={})
        .execute()
    )

    # Extract existing bindings
    bindings = policy.get("bindings", [])
    for role in roles:
        # Check if the role is already assigned
        binding = next((b for b in bindings if b["role"] == role), None)
        if binding:
            members = binding.get("members", [])
            if f"serviceAccount:{service_account_email}" in members:
                print(
                    f"Role {role} already assigned to {service_account_email}. Skipping..."
                )
                continue
            else:
                # Add the service account to the existing binding
                binding["members"].append(f"serviceAccount:{service_account_email}")
        else:
            # Create a new binding if the role is not in the policy
            bindings.append(
                {"role": role, "members": [f"serviceAccount:{service_account_email}"]}
            )

    # Update the policy with the modified bindings
    policy["bindings"] = bindings

    # Push the updated policy back to GCP
    cloud_resource_manager.projects().setIamPolicy(
        resource=project_id, body={"policy": policy}
    ).execute()

    print(f"Roles assigned successfully: {roles}")


def assign_impersonation_role(project_id, service_account_email, user_email):
    """
    Assign the Service Account User role to a user to allow them to act as the service account.

    Args:
        project_id (str): GCP Project ID.
        service_account_email (str): Email of the service account.
        user_email (str): Email of the user to allow acting as the service account.
    """
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    iam_service = build("iam", "v1", credentials=credentials)

    # Get the current IAM policy for the service account
    resource = f"projects/{project_id}/serviceAccounts/{service_account_email}"
    policy = (
        iam_service.projects()
        .serviceAccounts()
        .getIamPolicy(resource=resource)
        .execute()
    )

    # Check if the user already has the role
    bindings = policy.get("bindings", [])
    role = "roles/iam.serviceAccountUser"
    binding = next((b for b in bindings if b["role"] == role), None)
    if binding:
        members = binding.get("members", [])
        if f"user:{user_email}" in members:
            print(
                f"User {user_email} already has 'roles/iam.serviceAccountUser' on {service_account_email}. Skipping..."
            )
            return
        else:
            binding["members"].append(f"user:{user_email}")
    else:
        # Add a new binding for the role
        bindings.append({"role": role, "members": [f"user:{user_email}"]})

    # Update the policy with the modified bindings
    policy["bindings"] = bindings
    iam_service.projects().serviceAccounts().setIamPolicy(
        resource=resource, body={"policy": policy}
    ).execute()

    print(
        f"User {user_email} granted 'roles/iam.serviceAccountUser' on {service_account_email}."
    )
