# 3-Group Bayesian Hierarchical DDM, Standard Model
# Manning's EXACT centred parameterisation extended to 3 groups
#
# Based directly on:
#   MODEL_DIFF-BayesHier-cathyAutism-task_coherence.R
#   MODEL_DIFF-BayesHier-cathyDyslexia-task_coherence.R
#
# Changes from Manning's 2-group script:
#   - 3 groups: TD (0), Autism (1), Dyslexia (2)
#   - Two change params per DDM param: changeA, changeD
#   - TD pooled and deduplicated from both datasets
#   - n.hpars = 5 params x 4 hyperparams (mu,sigma,changeA,changeD) = 20
#   - Extended to 6000 iter / 2500 burn-in for 3-group complexity
#
# Run twice:
#   task_num <- 1; task_label <- "coherence"
#   task_num <- 2; task_label <- "deviation"
#
# Output:
#   FIT_DIFF-BayesHier-3group-Manning-standard-coherence.Rdata
#   3group_Manning_standard_coherence.csv
#
# Note: the paths should be set by the user


library(msm)
library(foreach)
library(doParallel)
library(rtdists)

set.seed(2024)

# TEST MODE 
test_mode <- FALSE

# 0. Paths
autism_csv   <- "path/to/Data_Matched_Round2_Autism.csv"
dyslexia_csv <- "path/to/BehavData_Matched_Round2_Dyslexia.csv"

if (!exists("task_num"))   task_num   <- 1
if (!exists("task_label")) task_label <- "coherence"

out_dir <- file.path("your_path/", task_label, fsep = "/")
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

n_cores <- if (exists("n_cores_use")) n_cores_use else 5
registerDoParallel(cores = n_cores)

# 1. Load and pool data
load_behav <- function(path, recode_clinical_to) {
  tmp <- read.csv(path)
  if ("ID"    %in% colnames(tmp)) tmp$subj <- as.character(tmp$ID)
  else                             tmp$subj <- as.character(tmp$subj)
  if ("Group" %in% colnames(tmp)) tmp$group <- as.integer(tmp$Group)
  else                             tmp$group <- as.integer(tmp$group)
  
  tmp$group <- ifelse(tmp$group == 1L, as.integer(recode_clinical_to), 0L)
  tmp <- tmp[tmp$task == task_num, ]
  tmp <- tmp[tmp$cond %in% c(1, 2), ]
  tmp <- tmp[!is.na(tmp$accuracy) & !is.nan(tmp$accuracy), ]
  tmp <- tmp[tmp$RT > 0, ]
  
  data.frame(
    subj      = tmp$subj,
    group     = tmp$group,
    condition = as.integer(tmp$cond),
    acc       = as.integer(tmp$accuracy),
    rt        = tmp$RT,
    stringsAsFactors = FALSE
  )
}

dat_autism   <- load_behav(autism_csv,   recode_clinical_to = 1)
dat_dyslexia <- load_behav(dyslexia_csv, recode_clinical_to = 2)
dat_all      <- rbind(dat_autism, dat_dyslexia)

# Deduplicate shared TD participants
dat_all <- dat_all[!duplicated(paste(dat_all$subj, dat_all$condition, dat_all$rt)), ]

# TEST MODE: 5 subjects per group
if (test_mode) {
  keep <- c(
    sample(unique(dat_all$subj[dat_all$group == 0]), 5),
    sample(unique(dat_all$subj[dat_all$group == 1]), 5),
    sample(unique(dat_all$subj[dat_all$group == 2]), 5)
  )
  dat_all <- dat_all[dat_all$subj %in% keep, ]
  cat("*** TEST MODE: 15 subjects only ***\n\n")
}

# Subject-level info
subj_info <- dat_all[!duplicated(dat_all$subj), c("subj", "group")]
subj_info <- subj_info[order(subj_info$subj), ]

# Manning uses character group labels: "0", "1", "2"
group.perSub <- as.character(subj_info$group)
subs         <- subj_info$subj
S            <- length(subs)
groups       <- c("0", "1", "2")

# Per-subject data list — matching Manning's data[[j]] structure
data <- lapply(subs, function(s) dat_all[dat_all$subj == s, ])

n_td  <- sum(group.perSub == "0")
n_aut <- sum(group.perSub == "1")
n_dys <- sum(group.perSub == "2")

cat(sprintf("\n3-Group DDM (Manning centred) | Task: %s | Standard model\n", task_label))
cat(sprintf("N — TD: %d | Autism: %d | Dyslexia: %d | Total: %d\n",
            n_td, n_aut, n_dys, S))
cat(sprintf("Total trials: %d\n\n", nrow(dat_all)))

# 2. Parameter setup — matching Manning exactly
# Manning: theta.names = c("v.mean","a","ter","v.diff","beta")
# Manning: phi.names   = paste(theta.names, c("mu","sigma","change"))
# 3-group extension: two change params — changeA (autism), changeD (dyslexia)
# phi.names = paste(theta.names, c("mu","sigma","changeA","changeD"))

theta.names <- c("v.mean", "a", "ter", "v.diff", "beta")
n.pars      <- length(theta.names)  # 5

phi.names <- paste(rep(theta.names, each = 4),
                   c("mu", "sigma", "changeA", "changeD"), sep = ".")
n.hpars   <- length(phi.names)  # 20

# Manning's exact bounds
lower.bounds <- c(v.mean = -Inf, a = 0, ter = 0, v.diff = -Inf, beta = 0)
upper.bounds <- c(v.mean =  Inf, a = Inf, ter = Inf, v.diff = Inf, beta = 1)
names(lower.bounds) <- names(upper.bounds) <- theta.names

# Manning's maxRT
maxRT <- 2.5

# 3. Log-likelihood — Manning's exact ddiffusion/pdiffusion
# s = 0.1 fixed as Manning specifies
log.dens.like <- function(x, subj_data, par.names) {
  names(x) <- par.names
  
  v.mean <- x["v.mean"]; v.diff <- x["v.diff"]
  a      <- x["a"];      beta   <- x["beta"];  ter <- x["ter"]
  
  if (a <= 0 || ter <= 0 || beta <= 0 || beta >= 1) return(-Inf)
  
  out <- 0
  for (cond_num in c(1, 2)) {
    rows <- subj_data[subj_data$condition == cond_num, ]
    if (nrow(rows) == 0) next
    
    v <- if (cond_num == 1) v.mean - v.diff / 2   # hard
    else               v.mean + v.diff / 2   # easy
    z <- beta * a
    
    # Observed trials — matching Manning's ddiffusion call exactly
    ll <- ddiffusion(
      rt       = rows$rt,
      response = rows$acc + 1,  # Manning: correct=1→resp=2, error=0→resp=1
      z = z, a = a, v = v, t0 = ter, s = 0.1
    )
    out <- out + sum(log(pmax(ll, 1e-10)))
    
    # Non-responses — Manning's survivor function approach
    n_miss <- sum(rows$rt > maxRT)
    if (n_miss > 0) {
      surv <- 1 -
        pdiffusion(rt = maxRT, response = 2, z = z, a = a, v = v,
                   t0 = ter, s = 0.1) -
        pdiffusion(rt = maxRT, response = 1, z = z, a = a, v = v,
                   t0 = ter, s = 0.1)
      out <- out + n_miss * log(max(surv, 1e-10))
    }
  }
  out
}

# 4. Log-prior — Manning's dtnorm, extended to 3 groups 
# Manning 2-group:
#   group "0" (TD):       mean = mu - change/2
#   group "1" (clinical): mean = mu + change/2
#
# 3-group extension:
#   group "0" (TD):      mean = mu               (reference)
#   group "1" (Autism):  mean = mu + changeA
#   group "2" (Dyslexia):mean = mu + changeD

log.dens.prior <- function(x, hyper, group) {
  names(x) <- theta.names
  out <- 0
  for (p in theta.names) {
    mu_p      <- hyper[paste(p, "mu",      sep = ".")]
    sigma_p   <- hyper[paste(p, "sigma",   sep = ".")]
    changeA_p <- hyper[paste(p, "changeA", sep = ".")]
    changeD_p <- hyper[paste(p, "changeD", sep = ".")]
    
    group_mean <- mu_p +
      as.numeric(group == "1") * changeA_p +
      as.numeric(group == "2") * changeD_p
    
    out <- out + dtnorm(x[p], group_mean, sigma_p,
                        lower.bounds[p], upper.bounds[p], log = TRUE)
  }
  out
}

# Hyperprior — Manning's log.dens.hyper extended to 3 groups
log.dens.hyper <- function(theta_vec, phi_vec, prior, p, use.groupings) {
  # theta_vec: individual param values across all S subjects [length S]
  # phi_vec:   hyperparams for this param [mu, sigma, changeA, changeD]
  mu_p      <- phi_vec[paste(p, "mu",      sep = ".")]
  sigma_p   <- phi_vec[paste(p, "sigma",   sep = ".")]
  changeA_p <- phi_vec[paste(p, "changeA", sep = ".")]
  changeD_p <- phi_vec[paste(p, "changeD", sep = ".")]
  
  if (sigma_p <= 0) return(-Inf)
  
  out <- 0
  for (j in seq_along(use.groupings)) {
    gm <- mu_p +
      as.numeric(use.groupings[j] == "1") * changeA_p +
      as.numeric(use.groupings[j] == "2") * changeD_p
    out <- out + dtnorm(theta_vec[j], gm, sigma_p,
                        lower.bounds[p], upper.bounds[p], log = TRUE)
  }
  
  # Hyperpriors — matching Manning exactly
  out <- out +
    dtnorm(mu_p,      prior$mu[1],     prior$mu[2],
           lower.bounds[p], upper.bounds[p], log = TRUE) +
    dgamma(sigma_p,   prior$sigma[1],  prior$sigma[2], log = TRUE) +
    dnorm(changeA_p,  prior$change[1], prior$change[2], log = TRUE) +
    dnorm(changeD_p,  prior$change[1], prior$change[2], log = TRUE)
  
  out
}

# 5. Manning's crossover functions — copied exactly, group labels updated 

crossover <- function(i, pars, use.theta, use.like, subj_data,
                      hyper, par.names, currIT, group) {
  # Manning: recompute likelihood every 5 iterations
  if (currIT %% 5 == 0)
    use.like[i] <- log.dens.like(use.theta[i, ], subj_data, par.names)
  
  use.weight <- use.like[i] +
    log.dens.prior(use.theta[i, ], hyper[i, ], group)
  
  gamma <- 2.38 / sqrt(2 * length(pars))
  index <- sample(setdiff(1:n.chains, i), 2, replace = FALSE)
  
  theta_prop       <- use.theta[i, ]
  theta_prop[pars] <- use.theta[i, pars] +
    gamma * (use.theta[index[1], pars] - use.theta[index[2], pars]) +
    runif(1, -b, b)
  
  prior.like <- log.dens.prior(theta_prop, hyper[i, ], group)
  
  if (prior.like > -Inf) {
    like <- log.dens.like(theta_prop, subj_data, par.names)
  } else {
    like <- -Inf
  }
  
  weight <- like + prior.like
  if (!is.finite(weight)) weight <- -Inf
  
  if (runif(1) < exp(weight - use.weight)) {
    use.theta[i, ] <- theta_prop
    use.like[i]    <- like
  }
  c(use.like[i], use.theta[i, ])
}

crossover_hyper <- function(i, pars, use.theta, use.phi,
                            prior, p, use.groupings) {
  use.weight <- log.dens.hyper(use.theta[i, ], use.phi[i, pars],
                               prior, p, use.groupings)
  gamma <- 2.38 / sqrt(2 * length(pars))
  index <- sample(setdiff(1:n.chains, i), 2, replace = FALSE)
  
  phi_prop       <- use.phi[i, ]
  phi_prop[pars] <- use.phi[i, pars] +
    gamma * (use.phi[index[1], pars] - use.phi[index[2], pars]) +
    runif(1, -b, b)
  
  weight <- log.dens.hyper(use.theta[i, ], phi_prop[pars],
                           prior, p, use.groupings)
  if (!is.finite(weight)) weight <- -Inf
  
  if (runif(1) < exp(weight - use.weight))
    use.phi[i, ] <- phi_prop
  use.phi[i, ]
}

migration.crossover <- function(pars, use.theta, use.like, subj_data,
                                hyper, par.names, group) {
  n.mig   <- ceiling(runif(1, 0, n.chains))
  use.chs <- sample(1:n.chains, n.mig)
  
  for (mi in 1:n.mig) {
    cur <- use.like[use.chs[mi]] +
      log.dens.prior(use.theta[use.chs[mi], pars], hyper[use.chs[mi], ], group)
    nc  <- if (mi == 1) n.mig else mi - 1
    nw  <- use.like[use.chs[nc]] +
      log.dens.prior(use.theta[use.chs[nc], pars], hyper[use.chs[mi], ], group)
    if (runif(1) < exp(nw - cur)) {
      use.theta[use.chs[mi], ] <- use.theta[use.chs[nc], ]
      use.like[use.chs[mi]]    <- use.like[use.chs[nc]]
    }
  }
  cbind(use.like, use.theta)
}

migration.crossover_hyper <- function(pars, use.theta, use.phi,
                                      prior, p, use.groupings) {
  n.mig   <- ceiling(runif(1, 0, n.chains))
  use.chs <- sample(1:n.chains, n.mig)
  
  for (mi in 1:n.mig) {
    cur <- log.dens.hyper(use.theta[use.chs[mi], ], use.phi[use.chs[mi], pars],
                          prior, p, use.groupings)
    nc  <- if (mi == 1) n.mig else mi - 1
    nw  <- log.dens.hyper(use.theta[use.chs[mi], ], use.phi[use.chs[nc], pars],
                          prior, p, use.groupings)
    if (runif(1) < exp(nw - cur))
      use.phi[use.chs[mi], pars] <- use.phi[use.chs[nc], pars]
  }
  use.phi
}

# 6. Priors — Manning's exact prior list 
prior <- list(
  v.mean = list(mu = c(0.3, 0.3), sigma = c(1, 1), change = c(0, 0.01)),
  a      = list(mu = c(0.2, 0.2), sigma = c(1, 1), change = c(0, 0.01)),
  ter    = list(mu = c(0.3, 0.3), sigma = c(1, 1), change = c(0, 0.01)),
  v.diff = list(mu = c(0.0, 0.1), sigma = c(1, 1), change = c(0, 0.01)),
  beta   = list(mu = c(0.5, 0.2), sigma = c(1, 1), change = c(0, 0.01))
)

# 7. MCMC settings 
n.chains <- 15
n.pars   <- 5
n.hpars  <- 20     # 5 params x 4 hyperparams (mu,sigma,changeA,changeD)
nmc      <- 6000   # Manning uses 4000; extended for 3-group complexity
burnin   <- 2500

migration.start <- 500
migration.end   <- 1100
migration.freq  <- 14
b               <- 0.001

if (test_mode) { nmc <- 300; burnin <- 100 }

# Storage - matching Manning's dimension order exactly
# theta[chain, param, subj, iter]
# phi[chain, hpar, iter]
start.points <- c(v.mean = 0.3, a = 0.2, ter = 0.3, v.diff = 0.0, beta = 0.5)

theta  <- array(NA,   dim = c(n.chains, n.pars, S, 2))
weight <- array(-Inf, dim = c(2, n.chains, S))
phi    <- array(NA,   dim = c(n.chains, n.hpars, nmc))

n_post     <- nmc - burnin
theta_post <- array(NA, dim = c(n.chains, n.pars, S, n_post))

dimnames(theta)[[2]]      <- theta.names
dimnames(theta_post)[[2]] <- theta.names
dimnames(phi)[[2]]        <- phi.names

# 8. Initialise chains - Manning's rtnorm approach exactly 
cat("Initialising chains...\n")

for (i in 1:n.chains) {
  
  # Individual params — Manning's exact while loop with rtnorm
  temp <- foreach(j = 1:S,
                  .packages = c("msm", "rtdists")) %dopar% {
                    cur.weight <- -Inf
                    cur.theta  <- NULL
                    while (cur.weight == -Inf) {
                      cur.theta <- rtnorm(n     = n.pars,
                                          mean  = start.points,
                                          sd    = (start.points / 5) + 0.05,
                                          lower = lower.bounds,
                                          upper = upper.bounds)
                      names(cur.theta) <- theta.names
                      cur.weight <- log.dens.like(cur.theta, data[[j]],
                                                  par.names = theta.names)
                    }
                    c(cur.weight, cur.theta)
                  }
  
  for (j in 1:S) {
    theta[i, , j, 1] <- temp[[j]][2:(n.pars + 1)]  # slot 1 = iteration 1
    weight[1, i, j]  <- temp[[j]][1]               # slot 1 = iteration 1
  }
  
  # Hyperparams — Manning's exact grep-based initialisation
  # extended to cover changeA and changeD
  
  tmp <- grep("^a\\.",      phi.names); phi[i, tmp, 1] <- rtnorm(length(tmp), .2, .2, 0, Inf)
  tmp <- grep("v\\.mean\\.",phi.names); phi[i, tmp, 1] <- rtnorm(length(tmp), .3, .3, -Inf, Inf)
  tmp <- grep("ter\\.",     phi.names); phi[i, tmp, 1] <- rtnorm(length(tmp), .3, .3, 0, Inf)
  tmp <- grep("v\\.diff\\.",phi.names); phi[i, tmp, 1] <- rtnorm(length(tmp), 0,  .1, -Inf, Inf)
  tmp <- grep("beta\\.",    phi.names); phi[i, tmp, 1] <- rtnorm(length(tmp), .5, .2, 0, 1)
  
  # Overwrite sigma slots with positive values
  tmp <- grep("\\.sigma$",  phi.names); phi[i, tmp, 1] <- rtnorm(length(tmp), 0, .5, 0, Inf)
  # Overwrite change slots with near-zero values
  tmp <- grep("\\.changeA$",phi.names); phi[i, tmp, 1] <- rnorm(length(tmp), 0, .1)
  tmp <- grep("\\.changeD$",phi.names); phi[i, tmp, 1] <- rnorm(length(tmp), 0, .1)
  
  cat(sprintf("  Chain %d/%d initialised\n", i, n.chains))
}
cat("Initialisation complete.\n\n")

# 9. DE-MCMC — Manning's exact loop structure, memory-efficient 
savefile <- file.path(out_dir,
                      sprintf("FIT_DIFF-BayesHier-3group-Manning-standard-%s.Rdata", task_label))

cat(sprintf("Running DE-MCMC | %d iter | %d burn-in | %d chains | %d cores\n\n",
            nmc, burnin, n.chains, n_cores))

begin <- date()

for (i in 2:nmc) {
  
  # Manning-style per-iteration printing
  cat("\n ", i, " ")
  if (i %% 100 == 0) {
    cat(sprintf("  [%d/%d]", i, nmc))
    theta_cur <- theta[, , , 2]
    save(theta_cur, phi, weight, subs, group.perSub,
         theta.names, phi.names, file = savefile)
  }
  
  phi[, , i] <- phi[, , i - 1]
  rand.samp  <- sample(1:n.chains, n.chains)
  
  #  Update hyperparameters — Manning's per-parameter loop
  for (p in theta.names) {
    which.theta <- match(p, theta.names)
    which.phi   <- match(
      paste(p, c("mu", "sigma", "changeA", "changeD"), sep = "."),
      phi.names
    )
    
    # Use slot 1 (previous iteration)
    use.theta.p <- theta[rand.samp, which.theta, , 1]
    
    if (i %% migration.freq == 0 &&
        i > migration.start && i < migration.end) {
      phi[, , i] <- migration.crossover_hyper(
        pars          = which.phi,
        use.theta     = use.theta.p,
        use.phi       = phi[, , i],
        prior         = prior[[p]],
        p             = p,
        use.groupings = group.perSub
      )
    } else {
      phi[, , i] <- t(sapply(1:n.chains, crossover_hyper,
                             pars          = which.phi,
                             use.theta     = use.theta.p,
                             use.phi       = phi[, , i],
                             prior         = prior[[p]],
                             p             = p,
                             use.groupings = group.perSub
      ))
    }
  }
  
  #  Update individual parameters — Manning's for each over subjects 
  rand.samp2 <- sample(1:n.chains, n.chains)
  hyper      <- phi[rand.samp2, , i]
  
  if (i %% migration.freq == 0 &&
      i > migration.start && i < migration.end) {
    temp <- foreach(j = 1:S,
                    .export  = c("n.chains", "theta", "weight", "hyper", "data",
                                 "theta.names", "phi.names", "lower.bounds", "upper.bounds",
                                 "b", "maxRT", "group.perSub",
                                 "log.dens.like", "log.dens.prior", "migration.crossover"),
                    .packages = c("msm", "rtdists")
    ) %dopar% {
      migration.crossover(
        pars      = 1:n.pars,
        use.theta = theta[, , j, 1],    # slot 1 = previous
        use.like  = weight[1, , j],     # slot 1 = previous
        subj_data = data[[j]],
        hyper     = hyper,
        par.names = theta.names,
        group     = group.perSub[j]
      )
    }
  } else {
    temp <- foreach(j = 1:S,
                    .export  = c("n.chains", "theta", "weight", "hyper", "data",
                                 "theta.names", "phi.names", "lower.bounds", "upper.bounds",
                                 "b", "i", "maxRT", "group.perSub",
                                 "log.dens.like", "log.dens.prior", "crossover"),
                    .packages = c("msm", "rtdists")
    ) %dopar% {
      t(sapply(1:n.chains, crossover,
               pars      = 1:n.pars,
               use.theta = theta[, , j, 1],    # slot 1 = previous
               use.like  = weight[1, , j],     # slot 1 = previous
               subj_data = data[[j]],
               hyper     = hyper,
               par.names = theta.names,
               currIT    = i,
               group     = group.perSub[j]
      ))
    }
  }
  
  # Write into slot 2 (current)
  for (j in 1:S) {
    weight[2, , j]  <- temp[[j]][, 1]
    theta[, , j, 2] <- temp[[j]][, 2:(n.pars + 1)]
  }
  
  # Accumulate post-burnin theta
  if (i > burnin) theta_post[, , , i - burnin] <- theta[, , , 2]
  
  # Roll: current → previous
  theta[, , , 1] <- theta[, , , 2]
  weight[1, , ]  <- weight[2, , ]
}

cat("\nSampling complete.\n")
cat(sprintf("Started: %s\nFinished: %s\n", begin, date()))

# 10. Final save 
theta_cur <- theta[, , , 2]
save(phi, theta_post, theta_cur, weight,
     subs, group.perSub, theta.names, phi.names,
     burnin, nmc, file = savefile)
cat(sprintf("Saved: %s\n", savefile))

# 11. R-hat 
post_phi <- phi[, , (burnin + 1):nmc, drop = FALSE]

gelman_rubin <- function(arr3d, idx) {
  x <- arr3d[, , idx]; n <- ncol(x)
  B <- n * var(rowMeans(x)); W <- mean(apply(x, 1, var))
  sqrt(((n - 1) / n * W + B / n) / W)
}

rhats <- sapply(1:n.hpars, function(k) gelman_rubin(post_phi, k))
names(rhats) <- phi.names

cat("\n=== R-hat (hyperparameters) ===\n")
print(round(rhats, 3))
cat(sprintf("Max R-hat: %.3f\n", max(rhats)))
if (max(rhats) < 1.2) cat("All R-hats < 1.2\n") else
  cat("R-hats >= 1.2 — consider more iterations\n")

# 12. Posterior summary + BFs 
# Savage-Dickey BF for changeA and changeD parameters
savage_BF <- function(samples, pr_sd) {
  dnorm(0, mean(samples), sd(samples)) / dnorm(0, 0, pr_sd)
}

summary_rows <- lapply(phi.names, function(h) {
  x     <- as.vector(post_phi[, match(h, phi.names), ])
  pr_sd <- if (grepl("changeA$|changeD$", h)) 0.01 else NA
  BF    <- if (!is.na(pr_sd)) savage_BF(x, pr_sd) else NA
  data.frame(
    param = h,
    mean  = mean(x),
    sd    = sd(x),
    ci_lo = quantile(x, 0.025),
    ci_hi = quantile(x, 0.975),
    BF    = BF
  )
})
summary_df <- do.call(rbind, summary_rows)
rownames(summary_df) <- NULL

cat("\n Posterior Summary + Bayes Factors \n")
cat("(BF > 3: evidence | 1/3-3: inconclusive | < 1/3: null)\n\n")
print(summary_df, digits = 3)

write.csv(summary_df,
          file.path(out_dir,
                    sprintf("3group_Manning_standard_%s.csv", task_label)),
          row.names = FALSE)

cat(sprintf("\n Done. Results saved to: %s\n", out_dir))
