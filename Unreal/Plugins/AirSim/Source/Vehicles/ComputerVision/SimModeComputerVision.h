#pragma once

#include "CoreMinimal.h"

// #include <cstdlib>
// #include <cstdio>
#include "ComputerVisionPawn.h"
#include "common/Common.hpp"
#include "api/VehicleSimApiBase.hpp"
#include "SimMode/SimModeBase.h"

#include "SimModeComputerVision.generated.h"

UCLASS()
class AIRSIM_API ASimModeComputerVision : public ASimModeBase
{
    GENERATED_BODY()

// public:
//     // ASimModeComputerVision();
//     virtual void BeginPlay() override;

private:
    typedef AComputerVisionPawn TVehiclePawn;

//     struct FieldConfig {
//         std::array<double, 2> corner;
//         std::array<double, 2> size;

//         int lane_count;
//         double global_spacing;
//         int batch_size;
//         double length;
//         double local_spacing;

//         std::string default_crop_type;
//         std::vector<std::string> crop_type_paths;
//     };

//     FieldConfig field_cfg;

//     UPROPERTY(EditDefaultsOnly, Category = "Spawning")
//     TSubclassOf<AActor> DefaultSplineActor;

//     UPROPERTY()
//     UClass *spline_geometry;

// protected:
//     UFUNCTION()
//     void SpawnSpline(FVector loc, FRotator rot, int type_id);

protected:
    virtual std::unique_ptr<msr::airlib::ApiServerBase> createApiServer() const override;
    virtual void getExistingVehiclePawns(TArray<AActor*>& pawns) const override;
    virtual bool isVehicleTypeSupported(const std::string& vehicle_type) const override;
    virtual std::string getVehiclePawnPathName(const AirSimSettings::VehicleSetting& vehicle_setting) const override;
    virtual PawnEvents* getVehiclePawnEvents(APawn* pawn) const override;
    virtual const common_utils::UniqueValueMap<std::string, APIPCamera*> getVehiclePawnCameras(APawn* pawn) const override;
    virtual void initializeVehiclePawn(APawn* pawn) override;
    virtual std::unique_ptr<PawnSimApi> createVehicleSimApi(
        const PawnSimApi::Params& pawn_sim_api_params) const override;
    virtual msr::airlib::VehicleApiBase* getVehicleApi(const PawnSimApi::Params& pawn_sim_api_params,
                                                       const PawnSimApi* sim_api) const override;
};
