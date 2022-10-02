// Copyright (c) Microsoft Corporation. All rights reserved.
// Licensed under the MIT License.

#include "SimModeComputerVision.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/World.h"

#include "AirBlueprintLib.h"
#include "common/AirSimSettings.hpp"
#include "PawnSimApi.h"
#include "AirBlueprintLib.h"
#include "common/Common.hpp"
#include "common/EarthUtils.hpp"
#include "api/VehicleSimApiBase.hpp"
#include "common/AirSimSettings.hpp"
#include "physics/Kinematics.hpp"
#include "api/RpcLibServerBase.hpp"

// #include "JsonUtilities.h"

// ASimModeComputerVision::ASimModeComputerVision() : ASimModeBase()
// {
//     // static ConstructorHelpers::FClassFinder<APIPCamera> external_camera_class(TEXT("Blueprint'/AirSim/Blueprints/BP_PIPCamera'"));
//     // external_camera_class_ = external_camera_class.Succeeded() ? external_camera_class.Class : nullptr;

//     TSubobject<UStaticMeshComponent> default_crop_mesh = CreateDefaultSubobject<UStaticMeshComponent>(this, TEXT("DefaultMesh"));
//     const ConstructorHelpers::FObjectFinder<UStaticMesh> default_crop_mesh_obj(TEXT(field_cfg.default_crop_type.c_str()));
//     default_crop_mesh->SetStaticMesh(default_crop_mesh_obj);
// }

// void ASimModeComputerVision::BeginPlay() 
// {
//     Super::BeginPlay();

//     const FString json_file_path = std::string(getenv("HOME")) + "/Documents/AirSim/rtsp_opts.json";
//     FString json_data;

//     FFileHelper::LoadFileToString(json_data, *json_file_path);

//     TSharedPtr<FJsonObject> json_object = MakeSharable(new FJsonObject());
//     TSharedPtr<TJsonReader<> > json_reader = TJsonReaderFactory<>::Create(json_data);

//     if (FJsonSerializer::Deserialize(json_reader, json_object) && json_object.IsValid()) {
//         field_cfg.corner = json_object->GetArrayField("field_corner");
//         field_cfg.size = json_object->GetArrayField("field_size");

//         field_cfg.lane_count = json_object->GetIntegerField("lane_count");
//         field_cfg.length = json_object->GetNumberField("lane_length");
//         field_cfg.batch_size = json_object->GetNumberField("lane_thickness");
//         field_cfg.local_spacing = json_object->GetNumberField("local_spacing");
//         field_cfg.global_spacing = json_object->GetNumberField("global_spacing");

//         field_cfg.default_crop_type = json_object->GetStringField("default_crop_type");
//         field_cfg.crop_type_paths = json_object->GetArrayField("crop_types");

//         GLog->Log("Field Config:");
//         GLog->Log("\t- Corner: (" + field_cfg.corner[0] + ", " + field_cfg.corner[1] + ")");
//         GLog->Log("\t- Size (W, H): (" + field_cfg.size[0] + ", " + field_cfg.size[1] + ")");

//         GLog->Log("\t- # Lanes: " + field_cfg.lane_count);
//         GLog->Log("\t- # In Lanes: " + field_cfg.batch_size);
//         GLog->Log("\t- Lane length: " + field_cfg.length);
//         GLog->Log("\t- Local spacing: " + field_cfg.local_spacing);
//         GLog->Log("\t- Global spacing: " + field_cfg.global_spacing);

//         GLog->Log("Parsed config successfully.");
//     } else {
//         GLog->Log("WARNING: Couldn't deserialize json file!");
//         return;
//     }

//     // Load lane and spline geometry classes / meshes
//     // TSubobject<UStaticMeshComponent> default_crop_mesh = CreateDefaultSubobject<UStaticMeshComponent>(this, TEXT("DefaultMesh"));
//     // const ConstructorHelpers::FObjectFinder<UStaticMesh> default_crop_mesh_obj(TEXT(field_cfg.default_crop_type.c_str()));
//     // default_crop_mesh->SetStaticMesh(default_crop_mesh_obj);

//     int num_crop_types = field_cfg.crop_types.size();
//     FVector location(field_cfg.corner[0] * 100.0, field_cfg.corner[1] * 100.0, 100.0);
//     FRotator rotation(0.0);

//     for (int i = 0; i < field_cfg.lane_count; i++) {
//         // LaneBatch lane_i;
//         // lane_i.resize(field_cfg.batch_size);

//         for (int j = 0; j < field_cfg.batch_size; j++) {
//             // GetWorld()->SpawnActor<AActor>(lane_i[j], GetActorTransform());

//             double y_pos_in_m = field_cfg.corner[1] + i * field_cfg.global_spacing + j * field_cfg.local_spacing;
//             SpawnSpline(FVector(field_cfg.corner[0] * 100.0, 
//                                 y_pos_in_m * 100.0, 
//                                 100.0), 
//                         FRotator(0.0), 
//                         i % field_cfg.lane_count);
//         }
//     }
// }

// void ASimModeComputerVision::SpawnSpline(FVector loc, FRotator rot, int type_id) 
// {
//     printf("Requested a spline spawn at (%.3f, %.3f)...\n", loc.X, loc.Y);

//     FActorSpawnPArameters spawn_params;
//     AActor *spawned_spline_ref = GetWorld()->SpawnActor<AActor>(DefaultSplineActor, loc, rot, spawn_params);

//     UProperty *mesh_property = spawned_spline_ref->GetClass()->FindPropertyByName();

//     // Set crop type from type_id
//     // field_cfg.crop_types[type_id]

//     printf("Spawned spline.");
// }

std::unique_ptr<msr::airlib::ApiServerBase> ASimModeComputerVision::createApiServer() const
{
#ifdef AIRLIB_NO_RPC
    return ASimModeBase::createApiServer();
#else
    return std::unique_ptr<msr::airlib::ApiServerBase>(new msr::airlib::RpcLibServerBase(
        getApiProvider(), getSettings().api_server_address, getSettings().api_port));
#endif
}

void ASimModeComputerVision::getExistingVehiclePawns(TArray<AActor*>& pawns) const
{
    UAirBlueprintLib::FindAllActor<TVehiclePawn>(this, pawns);
}

bool ASimModeComputerVision::isVehicleTypeSupported(const std::string& vehicle_type) const
{
    return vehicle_type == msr::airlib::AirSimSettings::kVehicleTypeComputerVision;
}

std::string ASimModeComputerVision::getVehiclePawnPathName(const AirSimSettings::VehicleSetting& vehicle_setting) const
{
    //decide which derived BP to use
    std::string pawn_path = vehicle_setting.pawn_path;
    if (pawn_path == "")
        pawn_path = "DefaultComputerVision";

    return pawn_path;
}

PawnEvents* ASimModeComputerVision::getVehiclePawnEvents(APawn* pawn) const
{
    return static_cast<TVehiclePawn*>(pawn)->getPawnEvents();
}
const common_utils::UniqueValueMap<std::string, APIPCamera*> ASimModeComputerVision::getVehiclePawnCameras(
    APawn* pawn) const
{
    return static_cast<const TVehiclePawn*>(pawn)->getCameras();
}
void ASimModeComputerVision::initializeVehiclePawn(APawn* pawn)
{
    static_cast<TVehiclePawn*>(pawn)->initializeForBeginPlay();
}

std::unique_ptr<PawnSimApi> ASimModeComputerVision::createVehicleSimApi(
    const PawnSimApi::Params& pawn_sim_api_params) const
{
    auto vehicle_sim_api = std::unique_ptr<PawnSimApi>(new PawnSimApi(pawn_sim_api_params));
    vehicle_sim_api->initialize();
    vehicle_sim_api->reset();
    return vehicle_sim_api;
}

msr::airlib::VehicleApiBase* ASimModeComputerVision::getVehicleApi(const PawnSimApi::Params& pawn_sim_api_params,
                                                                   const PawnSimApi* sim_api) const
{
    //we don't have real vehicle so no vehicle API
    return nullptr;
}
