# 3-Group Bayesian Hierarchical DDM — Partial-Age Model
# Matches Manning's exact code structure from:
#   MODEL_DIFF-BayesHier-cathyDyslexia-task_coherence-
#   partialOutAge_allParams.R
#
# Groups: TD (0), Autism (1), Dyslexia (2)
# Extended from Manning's 2-group to 3-group design.
#
# Key changes from Manning's 2-group script:
#   - 3 groups instead of 2 (TD=0, Autism=1, Dyslexia=2)
#   - Separate delta for autism (dA) and dyslexia (dD)
#   - TD pooled and deduplicated from both datasets
#   - n.hpars = 5 params x 4 hyperparams = 20
#
# Run twice:
#   task_num <- 1; task_label <- "coherence"
#   task_num <- 2; task_label <- "deviation"


library(msm)          # for rtnorm — Manning uses this
library(foreach)
library(doParallel)
library(rtdists)      # for ddiffusion/pdiffusion — Manning uses this

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

# 1. Load trial-level data 
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
    condition = as.integer(tmp$cond),   # 1=hard, 2=easy
    acc       = as.integer(tmp$accuracy),
    rt        = tmp$RT,
    age       = as.numeric(tmp$age),
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
  cat(" TEST MODE: 15 subjects only \n\n")
}

# Subject-level info (one row per subject)
subj_info <- dat_all[!duplicated(dat_all$subj), c("subj", "group", "age")]
subj_info <- subj_info[order(subj_info$subj), ]
subj_info$age[is.na(subj_info$age)] <- mean(subj_info$age, na.rm = TRUE)

# Manning uses raw age (not z-scored) in the lm() residuals
# because the lm() internally handles scaling
age.perSub   <- subj_info$age
group.perSub <- as.character(subj_info$group)  # "0", "1", "2" as Manning uses

subs  <- subj_info$subj
S     <- length(subs)
groups <- unique(group.perSub)  # c("0","1","2")

# Build per-subject data list (matching Manning's data[[j]] structure)
data <- lapply(subs, function(s) dat_all[dat_all$subj == s, ])

n_td  <- sum(group.perSub == "0")
n_aut <- sum(group.perSub == "1")
n_dys <- sum(group.perSub == "2")

cat(sprintf("\n3-Group DDM | Task: %s | Partial-Age (Manning method)\n", task_label))
cat(sprintf("N — TD: %d | Autism: %d | Dyslexia: %d | Total: %d\n",
            n_td, n_aut, n_dys, S))
cat(sprintf("Total trials: %d\n", nrow(dat_all)))
cat(sprintf("Age mean: %.2f | SD: %.2f\n\n",
            mean(age.perSub), sd(age.perSub)))

# 2. Parameter names (matching Manning exactly) 
theta.names <- c("v.mean", "a", "ter", "v.diff", "beta")
n.pars      <- length(theta.names)

# Manning's hyperparameter structure: mu, sigma, change per param
# For 3 groups we need TWO change params: changeA (autism), changeD (dyslexia)
# So: mu, sigma, changeA, changeD = 4 hyperparams per DDM param = 20 total
phi.names <- paste(rep(theta.names, each = 4),
                   c("mu", "sigma", "changeA", "changeD"), sep = ".")
n.hpars   <- length(phi.names)  # 20

# Bounds — matching Manning exactly
lower.bounds <- c(v.mean = -Inf, a = 0, ter = 0, v.diff = -Inf, beta = 0)
upper.bounds <- c(v.mean =  Inf, a = Inf, ter = Inf, v.diff = Inf, beta = 1)

# 3. MCMC settings (matching Manning, extended for 3-group complexity) 
n.chains <- 15
nmc      <- 6000
burnin   <- 2500

migration.start <- 500
migration.end   <- 1100
migration.freq  <- 14

b <- 0.001

if (test_mode) { nmc <- 300; burnin <- 100 }

# MEMORY-EFFICIENT STORAGE 
# Problem: theta[15 x 5 x 155 x 6000] = ~33GB — crashes RAM
# Solution: keeping Two iteration slots (current + previous) for theta/weight
#           and accumulate post-burnin phi samples separately
#
# theta[chain, param, subj, slot]  — slot 1=prev, slot 2=current
# phi_post[chain, hpar, post_iter] — only post-burnin samples stored
# weight[slot, chain, subj]        — slot 1=prev, slot 2=current

theta  <- array(NA,   dim = c(n.chains, n.pars, S, 2),
                dimnames = list(NULL, theta.names, subs, NULL))
weight <- array(-Inf, dim = c(2, n.chains, S))

# phi: still needs full history for R-hat — but phi is tiny
# phi[chain, hpar, iter] = 15 x 20 x 6000 = 1.8M doubles = ~14MB — fine
phi    <- array(NA,   dim = c(n.chains, n.hpars, nmc),
                dimnames = list(NULL, phi.names, NULL))

# Post-burnin theta accumulator for individual-level parameter extraction
n_post         <- nmc - burnin
theta_post     <- array(NA, dim = c(n.chains, n.pars, S, n_post),
                        dimnames = list(NULL, theta.names, subs, NULL))

# 4. Log-likelihood — matching Manning's ddiffusion/pdiffusion calls
maxRT <- 2.5  # Manning's 2500ms deadline

log.dens.like <- function(x, subj_data, par.names) {
  names(x) <- par.names
  
  v.mean <- x["v.mean"]; v.diff <- x["v.diff"]
  a      <- x["a"];      beta   <- x["beta"];  ter <- x["ter"]
  
  if (a <= 0 || ter <= 0 || beta <= 0 || beta >= 1) return(-Inf)
  
  v_easy <- v.mean + v.diff / 2
  v_hard <- v.mean - v.diff / 2
  z_easy <- beta * a
  z_hard <- beta * a   # Manning uses same beta for both conditions
  
  out <- 0
  for (cond_num in c(1, 2)) {
    tmp_rows <- subj_data[subj_data$condition == cond_num, ]
    if (nrow(tmp_rows) == 0) next
    
    v <- if (cond_num == 1) v_hard else v_easy
    z <- if (cond_num == 1) z_hard else z_easy
    
    # Observed trials
    ll_obs <- ddiffusion(
      rt       = tmp_rows$rt,
      response = tmp_rows$acc + 1,   # Manning: correct=1→response=2, error=0→response=1
      z = z, a = a, v = v, t0 = ter, s = 0.1
    )
    out <- out + sum(log(pmax(ll_obs, 1e-10)))
    
    # Non-responses (RT > maxRT) — Manning's survivor function approach
    n_miss <- sum(tmp_rows$rt > maxRT)
    if (n_miss > 0) {
      surv <- 1 - pdiffusion(rt = maxRT, response = 2,
                             z = z, a = a, v = v, t0 = ter, s = 0.1) -
        pdiffusion(rt = maxRT, response = 1,
                   z = z, a = a, v = v, t0 = ter, s = 0.1)
      out <- out + n_miss * log(max(surv, 1e-10))
    }
  }
  out
}

# 5. Manning's within-MCMC age residualisation 
# Matches Manning's log.dens.prior exactly, extended to 3 groups
# group: "0"=TD, "1"=Autism, "2"=Dyslexia
log.dens.prior <- function(x, hyper, group, sub, all.params) {
  names(x) <- theta.names
  out <- 0
  
  for (p in theta.names) {
    # Update current subject's value in the full parameter matrix
    all.params[p, sub] <- x[p]
    
    # Manning's key step: partial out age via lm residuals
    partialParam <- lm(all.params[p, ] ~ age.perSub)$residuals
    
    mu_p      <- hyper[paste(p, "mu",      sep = ".")]
    sigma_p   <- hyper[paste(p, "sigma",   sep = ".")]
    changeA_p <- hyper[paste(p, "changeA", sep = ".")]
    changeD_p <- hyper[paste(p, "changeD", sep = ".")]
    
    # Group mean: TD = mu, Autism = mu + changeA, Dyslexia = mu + changeD
    group_mean <- mu_p +
      as.numeric(group == "1") * changeA_p +
      as.numeric(group == "2") * changeD_p
    
    out <- out + dnorm(partialParam[sub], group_mean, sigma_p, log = TRUE)
  }
  out
}

# Hyperprior — matches Manning's log.dens.hyper, extended to 3 groups
log.dens.hyper <- function(theta_vec, phi_vec, prior, p, use.groupings) {
  # theta_vec: vector of one param across all subjects [S]
  # Partial out age
  use.theta <- lm(theta_vec ~ age.perSub)$residuals
  
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
    out <- out + dnorm(use.theta[j], gm, sigma_p, log = TRUE)
  }
  
  # Priors on hyperparameters — matching Manning's prior list exactly
  out <- out +
    dtnorm(mu_p,      prior$mu[1],     prior$mu[2],
           lower = lower.bounds[p], upper = upper.bounds[p], log = TRUE) +
    dgamma(sigma_p,   prior$sigma[1],  prior$sigma[2], log = TRUE) +
    dnorm(changeA_p,  prior$change[1], prior$change[2], log = TRUE) +
    dnorm(changeD_p,  prior$change[1], prior$change[2], log = TRUE)
  
  out
}

# 6. Manning's crossover functions
crossover <- function(i, pars, use.theta, use.like, subj_data,
                      hyper, par.names, currIT, group, all.params, sub) {
  # Recompute likelihood every 5 iterations (Manning's approach)
  if (currIT %% 5 == 0)
    use.like[i] <- log.dens.like(use.theta[i, ], subj_data, par.names)
  
  use.weight <- use.like[i] +
    log.dens.prior(use.theta[i, ], hyper[i, ], group, sub, all.params[i, , ])
  
  gamma <- 2.38 / sqrt(2 * length(pars))
  index <- sample(setdiff(1:n.chains, i), 2, replace = FALSE)
  
  theta_prop      <- use.theta[i, ]
  theta_prop[pars] <- use.theta[i, pars] +
    gamma * (use.theta[index[1], pars] - use.theta[index[2], pars]) +
    runif(1, -b, b)
  
  prior.like <- log.dens.prior(theta_prop, hyper[i, ], group, sub,
                               all.params[i, , ])
  
  if (prior.like > -Inf &&
      !any(theta_prop < lower.bounds) &&
      !any(theta_prop > upper.bounds)) {
    like <- log.dens.like(theta_prop, subj_data, par.names)
  } else {
    like <- -Inf
  }
  
  weight_prop <- like + prior.like
  if (!is.finite(weight_prop)) weight_prop <- -Inf
  
  if (runif(1) < exp(weight_prop - use.weight)) {
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
  
  weight_prop <- log.dens.hyper(use.theta[i, ], phi_prop[pars],
                                prior, p, use.groupings)
  if (!is.finite(weight_prop)) weight_prop <- -Inf
  
  if (runif(1) < exp(weight_prop - use.weight))
    use.phi[i, ] <- phi_prop
  use.phi[i, ]
}

migration.crossover <- function(pars, use.theta, use.like, subj_data,
                                hyper, par.names, group, all.params, sub) {
  n.mig   <- ceiling(runif(1, 0, n.chains))
  use.chs <- sample(1:n.chains, n.mig)
  mig.cur <- mig.new <- rep(NA, n.mig)
  
  for (mi in 1:n.mig) {
    mig.cur[mi] <- use.like[use.chs[mi]] +
      log.dens.prior(use.theta[use.chs[mi], pars], hyper[use.chs[mi], ],
                     group, sub, all.params[use.chs[mi], , ])
    nc <- if (mi == 1) n.mig else mi - 1
    mig.new[mi] <- use.like[use.chs[nc]] +
      log.dens.prior(use.theta[use.chs[nc], pars], hyper[use.chs[mi], ],
                     group, sub, all.params[use.chs[mi], , ])
    if (runif(1) < exp(mig.new[mi] - mig.cur[mi])) {
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
  mig.cur <- mig.new <- rep(NA, n.mig)
  
  for (mi in 1:n.mig) {
    mig.cur[mi] <- log.dens.hyper(use.theta[use.chs[mi], ], use.phi[use.chs[mi], pars],
                                  prior, p, use.groupings)
    nc <- if (mi == 1) n.mig else mi - 1
    mig.new[mi] <- log.dens.hyper(use.theta[use.chs[mi], ], use.phi[use.chs[nc], pars],
                                  prior, p, use.groupings)
    if (runif(1) < exp(mig.new[mi] - mig.cur[mi]))
      use.phi[use.chs[mi], pars] <- use.phi[use.chs[nc], pars]
  }
  use.phi
}

# 7. Priors (matching Manning's prior list exactly) 
start.points <- c(v.mean = 0.3, a = 0.2, ter = 0.3, v.diff = 0.0, beta = 0.5)

prior <- list(
  v.mean = list(mu = c(0.3, 0.3), sigma = c(1, 1), change = c(0, 0.01)),
  a      = list(mu = c(0.2, 0.2), sigma = c(1, 1), change = c(0, 0.01)),
  ter    = list(mu = c(0.3, 0.3), sigma = c(1, 1), change = c(0, 0.01)),
  v.diff = list(mu = c(0.0, 0.1), sigma = c(1, 1), change = c(0, 0.01)),
  beta   = list(mu = c(0.5, 0.2), sigma = c(1, 1), change = c(0, 0.01))
)

# 8. Initialise chains (matching Manning's rtnorm approach exactly) 
cat("Initialising chains...\n")

for (i in 1:n.chains) {
  # Individual parameters — using rtnorm like Manning
  temp <- foreach(j = 1:S, .packages = c("msm", "rtdists")) %dopar% {
    cur.weight <- -Inf
    cur.theta  <- NULL
    while (cur.weight == -Inf) {
      cur.theta <- rtnorm(n     = n.pars,
                          mean  = start.points,
                          sd    = (start.points / 5) + 0.05,
                          lower = lower.bounds,
                          upper = upper.bounds)
      names(cur.theta) <- theta.names
      cur.weight <- log.dens.like(cur.theta, data[[j]], par.names = theta.names)
    }
    c(cur.weight, cur.theta)
  }
  
  for (j in 1:S) {
    theta[i, , j, 1] <- temp[[j]][2:(n.pars + 1)]  # slot 1 = iteration 1
    weight[1, i, j]  <- temp[[j]][1]               # slot 1 = iteration 1
  }
  
  # Hyperparameters — matching Manning's group-specific phi initialisation
  for (p in theta.names) {
    mu_idx  <- match(paste(p, "mu",      sep = "."), phi.names)
    sig_idx <- match(paste(p, "sigma",   sep = "."), phi.names)
    cA_idx  <- match(paste(p, "changeA", sep = "."), phi.names)
    cD_idx  <- match(paste(p, "changeD", sep = "."), phi.names)
    
    phi[i, mu_idx,  1] <- rtnorm(1, prior[[p]]$mu[1],     prior[[p]]$mu[2],
                                 lower.bounds[p], upper.bounds[p])
    phi[i, sig_idx, 1] <- rtnorm(1, 0, 0.5, 0, Inf)
    phi[i, cA_idx,  1] <- rnorm(1, 0, 0.1)
    phi[i, cD_idx,  1] <- rnorm(1, 0, 0.1)
  }
  
  cat(sprintf("  Chain %d/%d initialised\n", i, n.chains))
}
cat("Initialisation complete.\n\n")

# ---- 9. DE-MCMC — Manning's loop structure, memory-efficient -----------------
# Rolling 2-slot storage: slot 1 = previous iter, slot 2 = current iter
# After each iteration: slot 2 → slot 1, ready for next iter
# Post-burnin: accumulate phi normally (tiny), accumulate theta_post separately

cat(sprintf("Running DE-MCMC | %d iter | %d burn-in | %d chains | %d cores\n\n",
            nmc, burnin, n.chains, n_cores))

savefile <- file.path(out_dir,
                      sprintf("FIT_DIFF-BayesHier-3group-pooledTD_partialAge-%s.Rdata", task_label))

begin <- date()

for (i in 2:nmc) {
  
  # Manning-style iteration printing — every iteration like her cat("\n", i, "  ")
  cat("\n ", i, " ")
  if (i %% 100 == 0) {
    cat(sprintf("  [%d/%d — elapsed since start]", i, nmc))
    # Periodic save — phi is small enough to save fully
    # theta: save only current slot
    theta_cur <- theta[, , , 2]   # current individual params
    save(theta_cur, phi, weight, subs, group.perSub, age.perSub,
         theta.names, phi.names, burnin, nmc, file = savefile)
  }
  
  phi[, , i] <- phi[, , i - 1]
  
  do_migration <- (i %% migration.freq == 0 &&
                     i > migration.start && i < migration.end)
  
  rand.samp <- sample(1:n.chains, n.chains)
  
  # Update hyperparameters (phi) — one param at a time like Manning
  for (p in theta.names) {
    which.phi <- match(paste(p, c("mu", "sigma", "changeA", "changeD"), sep = "."),
                       phi.names)
    
    # Use slot 1 (previous iteration) for theta
    use.theta.p <- theta[rand.samp, match(p, theta.names), , 1]
    
    if (do_migration) {
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
  
  # Update individual parameters (theta) — foreach over subjects 
  rand.samp2 <- sample(1:n.chains, n.chains)
  hyper      <- phi[rand.samp2, , i]
  
  if (do_migration) {
    temp <- foreach(j = 1:S,
                    .export  = c("n.chains", "theta", "weight", "hyper", "data",
                                 "theta.names", "phi.names", "lower.bounds", "upper.bounds",
                                 "age.perSub", "group.perSub", "b",
                                 "log.dens.like", "log.dens.prior", "migration.crossover"),
                    .packages = c("msm", "rtdists")
    ) %dopar% {
      migration.crossover(
        pars       = 1:n.pars,
        use.theta  = theta[, , j, 1],     # slot 1 = previous
        use.like   = weight[1, , j],      # slot 1 = previous
        subj_data  = data[[j]],
        hyper      = hyper,
        par.names  = theta.names,
        group      = group.perSub[j],
        all.params = theta[, , , 1],      # slot 1 = previous
        sub        = j
      )
    }
  } else {
    temp <- foreach(j = 1:S,
                    .export  = c("n.chains", "theta", "weight", "hyper", "data",
                                 "theta.names", "phi.names", "lower.bounds", "upper.bounds",
                                 "age.perSub", "group.perSub", "b", "i",
                                 "log.dens.like", "log.dens.prior", "crossover"),
                    .packages = c("msm", "rtdists")
    ) %dopar% {
      t(sapply(1:n.chains, crossover,
               pars       = 1:n.pars,
               use.theta  = theta[, , j, 1],     # slot 1 = previous
               use.like   = weight[1, , j],      # slot 1 = previous
               subj_data  = data[[j]],
               hyper      = hyper,
               par.names  = theta.names,
               currIT     = i,
               group      = group.perSub[j],
               all.params = theta[, , , 1],      # slot 1 = previous
               sub        = j
      ))
    }
  }
  
  # Write results into slot 2 (current)
  for (j in 1:S) {
    weight[2, , j]  <- temp[[j]][, 1]
    theta[, , j, 2] <- temp[[j]][, 2:(n.pars + 1)]
  }
  
  # Accumulate post-burnin theta samples
  if (i > burnin) {
    theta_post[, , , i - burnin] <- theta[, , , 2]
  }
  
  # Roll: slot 2 → slot 1 for next iteration
  theta[, , , 1] <- theta[, , , 2]
  weight[1, , ]  <- weight[2, , ]
}

cat("\nSampling complete.\n")
cat(sprintf("Started: %s\nFinished: %s\n", begin, date()))

# 10. Final save 
# Save phi (full chain history — small), theta_post (post-burnin only),
# and current theta slot for any further use
theta_cur <- theta[, , , 2]
save(phi, theta_post, theta_cur, weight,
     subs, group.perSub, age.perSub,
     theta.names, phi.names, burnin, nmc,
     file = savefile)
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

cat("\n R-hat (hyperparameters) \n")
print(round(rhats, 3))
cat(sprintf("Max R-hat: %.3f\n", max(rhats)))
if (max(rhats) < 1.2) cat("All R-hats < 1.2\n") else
  cat("R-hats >= 1.2 — consider more iterations\n")

# 12. Posterior summary + BFs 
savage_BF <- function(samples, pr_sd) {
  dnorm(0, mean(samples), sd(samples)) / dnorm(0, 0, pr_sd)
}

summary_rows <- lapply(phi.names, function(h) {
  x     <- as.vector(post_phi[, match(h, phi.names), ])
  pr_sd <- if (grepl("changeA$|changeD$", h)) 0.01 else NA
  BF    <- if (!is.na(pr_sd)) savage_BF(x, pr_sd) else NA
  data.frame(param = h, mean = mean(x), sd = sd(x),
             ci_lo = quantile(x, 0.025), ci_hi = quantile(x, 0.975),
             BF = BF)
})
summary_df <- do.call(rbind, summary_rows)
rownames(summary_df) <- NULL

cat("\n Posterior Summary + Bayes Factors \n")
cat("(BF > 3: evidence | 1/3-3: inconclusive | < 1/3: null)\n\n")
print(summary_df, digits = 3)

write.csv(summary_df,
          file.path(out_dir,
                    sprintf("3group_summary_partialAge_%s.csv", task_label)),
          row.names = FALSE)

cat(sprintf("\n Done. Results saved to: %s\n", out_dir))