#!/usr/bin/env python
import os
import json
import psycopg2


def fetch_hosts_from_db():
    try:
        # Each of these variables should be defined in a custom credential in Tower/AWX to securely store it. DO NOT HARD CODE IT HERE, you will put your company at risk.
        conn = psycopg2.connect(
            dbname=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USERNAME"),
            password=os.environ.get("DB_PASSWORD"),
            host=os.environ.get("DB_HOSTNAME"),
            port=os.environ.get("DB_PORT"),
        )
    except psycopg2.OperationalError as e:
        print(f"Database connection failed: {e}")
        return []

    cursor = conn.cursor()

    # Query used, stripped version with the needed info in it. In my case I am reaching out to a Database that a network team manages and reading the tags of each server, only returning the servers that have the specific tags.
    query = """
            SELECT
                d."Name" as "Datasource Name",
                a."ObjectId" as "VM Id",
                a."ObjectName" as "VM Name",
                cast(a."Object"::json AS json) -> 'tags as "Tags"
            FROM
                dbo."Objects" a
            INNER JOIN
                dbo."ObjectInventory" b ON a."InventoryId" = b."Id"
            INNER JOIN
                dbo."Datasource" d ON b."DatasourceId" = d."DatasourceId"
            WHERE
                a."SystemEntityId" = 3001
                AND b."CacheGroup" = 4
                AND d."ConnectionTypeId" IN (5, 8, 10)
                AND EXISTS (
                    SELECT 1
                    FROM jsonb_each_text(cast(a."Object"::jsonb AS jsonb) -> 'tags') AS kv
                    WHERE kv.value ILIKE '%TEAMNAME'

    );

    """

    # Execute the query
    cursor.execute(query)

    # Fetch the data
    sql_data = cursor.fetchall()

    # Close the connection
    conn.close()

    # Process the results and extract the TEAMNAME tag for each host
    json_like_data = []

    for row in sql_data:
        tags_raw = row[3] if row[3] else {}
        app_region = None

        # Check if tags_raw is a string that needs to be loaded as JSON
        if isinstance(tags_raw, str):
            try:
                tags_dict = json.loads(tags_raw)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from tags: {tags_raw} - {e}")
                continue
        elif isinstance(tags_raw, dict):
            # If it's already a dictionary, no need for json.loads
            tags_dict = tags_raw

        else:
            print(f"Unexepected type for tags data: {type(tags_raw)} - {tags_raw}")
            continue

        # Get the array of tags
        tags_array = tags_dict.get("$values", [])
        for tag in tags_array:
            tag_value = tag.get("tag", "")
            if tag_value.startswith(
                "TEAMNAME-"
            ):  # Check if the tag starts with "TEAMNAME-"
                app_region = tag_value
                break  # Once we found a match, we exit the loop

        json_like_data.append(
            {
                "Name": row[0],
                "ObjectId": row[1],
                "ObjectName": row[2],
                "app_region": app_region,
            }
        )

    return json_like_data


def generate_inventory(hosts):
    inventory = {"_meta": {"hostvars": {}}}

    # Here is where I would define the global variables I would like servers to have when imported into ansible
    for host in hosts:
        app_region = host.get("app_region")
        hostname = host.get("ObjectName")

        # Then I start separating them by environment based on what is present in the hostname. You could do it via the group or whatever standardization is present so long as that was standardized data you were pulling from the query and it is definined.
        if any(
            test_env in app_region or "TEST" in hostname
            for test_env in ["DEV", "TEST1", "TEST2"]
        ):
            groups = []
            # Change job_name to whatever you use for Prometheus, otherwise the job_name variable can be cleared out
            job_name = "generic-prometheus-job-name"
            # connected_hosts is a silly variable but it can allow for some automation regarding documenting what connects to what...  See my Visio generation script for more info. [[LINK]]
            connected_hosts = []
            ansible_control_hostname = "MY-ANSIBLE-SERVER.COM"
            grafana_hostname = "MY-GRAFANA-SERVER.COM"

            # Further sorting of environments, while not the cleanest way to do it, it is really easy to write out. But really, you should go back and clean it when you are done.
            if "DEV" in hostname:
                groups.extend(["DEV"])
                if "HTTP" or "WEB" in hostname:
                    groups.extend(["WEB", "WEB_PATCHING"])
                elif "APP" or "TOMCAT" in hostname:
                    groups.extend(["APP", "TOMCAT_PATCHING"])

            elif "TEST1" in hostname:
                groups.extend(["TEST1"])
                if "HTTP" or "WEB" in hostname:
                    groups.extend(["WEB", "WEB_PATCHING"])
                elif "APP" or "TOMCAT" in hostname:
                    groups.extend(["APP", "TOMCAT_PATCHING"])

            elif "TEST2" in hostname:
                groups.extend(["TEST2"])
                if "HTTP" or "WEB" in hostname:
                    groups.extend(["WEB", "WEB_PATCHING"])
                elif "APP" or "TOMCAT" in hostname:
                    groups.extend(["APP", "TOMCAT_PATCHING"])

        # Lastly, we want to catch anything that didn't work in the filter, so we may update the filter. This is a repetitive process, but necessary to create a strong filter for your ORG.
        else:
            hostname = host["ObjectName"]
            groups = "UNKNOWN"
            job_name = "generic-metrics"
            connected_hosts = []
            ansible_control_hostname = "UNKNOWN"
            grafana_hostname = "UNKNOWN"

        for group in groups:
            if group not in inventory:
                inventory[group] = {"hosts": []}
            inventory[group]["hosts"].append(hostname)

        # Define the host's varaibles
        inventory["_meta"]["hostvars"][hostname] = {
            "job_name": job_name,
            "env_name": env_name,
            "server_description": "Server in my org",
            "connected_hosts": connected_hosts,
        }

    return inventory


if __name__ == "__main__":
    hosts = fetch_hosts_from_db()
    inventory = generate_inventory(hosts)
    print(json.dumps(inventory))
